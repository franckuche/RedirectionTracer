import logging
import asyncio
import aiohttp
from .http_utils import trace_http_redirection_async, check_url_status

async def process_url_batch(item, session, target_status_results):
    """Traite une URL dans un lot."""
    # Vérifier que l'item est bien un dictionnaire
    if not isinstance(item, dict):
        logging.error(f"Erreur: item n'est pas un dictionnaire mais {type(item)}: {item}")
        return None
        
    try:
        # Récupérer les informations de l'URL
        line_num = item.get("line_num", 0)
        source_url = item.get("source", "")
        target_url = item.get("target", "")
        source_url_absolute = item.get("source_absolute", "")
        target_url_absolute = item.get("target_absolute", "")
        
        # Vérifier que les URLs sont valides
        if not source_url_absolute or not target_url_absolute:
            logging.error(f"URLs invalides pour la ligne {line_num}: source={source_url_absolute}, target={target_url_absolute}")
            return None
        
        # Tracer les redirections pour cette URL
        final_url, error_message, redirections_count, http_status = await trace_http_redirection_async(source_url_absolute, session)
        
        # Récupérer le statut HTTP de l'URL cible
        target_status = target_status_results.get(target_url_absolute, 0)
        
        # Utiliser le champ final existant comme fallback si la redirection échoue
        existing_final = item.get("final", "")
        
        # Log détaillé pour traçabilité
        logging.info(f"Ligne {line_num} - Résumé redirection: code={http_status} | source={source_url_absolute} -> finale={final_url if final_url is not None else existing_final if existing_final else 'N/A'} (attendue: {target_url_absolute})")
        
        # Déterminer le statut de la redirection
        if error_message:
            conclusion = f"ERREUR: {error_message}"
            final_display = existing_final if existing_final else "N/A"  # Utiliser le champ final existant comme fallback
            status = "ERREUR"
        elif final_url is None:
            conclusion = f"ERREUR: Impossible de suivre la redirection"
            final_display = existing_final if existing_final else "N/A"  # Utiliser le champ final existant comme fallback
            status = "ERREUR"
        # Vérifier si l'URL finale est identique à l'URL source (pas de redirection)
        elif final_url.rstrip('/') == source_url_absolute.rstrip('/'):
            # Vérifier si l'URL source correspond à l'URL cible (pas de redirection nécessaire)
            if source_url_absolute.rstrip('/') == target_url_absolute.rstrip('/'):
                conclusion = "CORRECT: Pas de redirection nécessaire, l'URL source est déjà l'URL cible."
                status = "CORRECT"
            else:
                conclusion = "INCORRECT: Aucune redirection, l'URL source reste inchangée mais ne correspond pas à l'URL cible."
                status = "INCORRECT"
            final_display = final_url
        # Vérifier si l'URL finale correspond à l'URL cible (redirection correcte)
        elif final_url.rstrip('/') == target_url_absolute.rstrip('/'):
            # Vérifier si le code HTTP est un succès (200-299) ou une redirection (300-399)
            if 200 <= http_status < 400:
                if redirections_count > 1:
                    conclusion = f"CORRECT (avec {redirections_count} redirections): La redirection aboutit bien à l'URL cible attendue."
                else:
                    conclusion = "CORRECT: La redirection aboutit bien à l'URL cible attendue."
                status = "CORRECT"
            else:
                # L'URL correspond mais le code HTTP indique une erreur
                conclusion = f"ERREUR: La redirection aboutit à l'URL cible attendue mais avec un code HTTP {http_status}."
                status = "ERREUR"
            final_display = final_url
        else:
            if redirections_count > 1:
                conclusion = f"INCORRECT (avec {redirections_count} redirections): La redirection aboutit à une URL différente de celle attendue."
            else:
                conclusion = "INCORRECT: La redirection aboutit à une URL différente de celle attendue."
            final_display = final_url
            status = "INCORRECT"
        
        # Ajouter le résultat
        result = {
            "line_num": line_num,
            "source": source_url,
            "target": target_url,
            "final": final_display if final_display is not None else "N/A",
            "redirections_count": redirections_count,
            "status": status,
            "http_status": http_status,
            "target_status": target_status,
            "conclusion": conclusion
        }
        
        # Log détaillé du résultat complet pour débogage
        logging.info(f"Ligne {line_num} - Résultat structuré = {result}")
        
        return result
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logging.error(f"Erreur lors du traitement de l'URL: {e}")
        logging.error(f"Détails de l'erreur: {error_details}")
        return None

async def process_urls_in_batches(urls_to_process, task_id, tasks):
    """
    Traite une liste d'URLs par lots.
    
    Args:
        urls_to_process (list): Liste des URLs à traiter
        task_id (str): ID de la tâche
        tasks (dict): Dictionnaire des tâches
        
    Returns:
        tuple: (details, stats)
    """
    # Initialiser les statistiques et les détails
    stats = {
        "total": len(urls_to_process),
        "correct_count": 0,
        "incorrect_count": 0,
        "error_count": 0,
        "multi_redirect_count": 0
    }
    details = []
    
    if stats["total"] == 0:
        return details, stats
    
    # Traiter les URLs par lots pour éviter de surcharger le serveur
    batch_size = 10  # Nombre d'URLs à traiter en parallèle
    
    # Vérifier le statut des URLs cibles en parallèle
    target_status_results = {}
    
    # Traiter les URLs par lots
    for i in range(0, len(urls_to_process), batch_size):
        batch_end = min(i + batch_size, len(urls_to_process))
        current_batch = urls_to_process[i:batch_end]
        
        # Mettre à jour le message de progression
        if task_id and tasks:
            tasks[task_id]["message"] = f"Traitement du lot {i+1}-{batch_end} sur {len(urls_to_process)} URLs..."
            tasks[task_id]["progress"] = (i / len(urls_to_process)) * 0.9  # 90% de la progression totale
        
        logging.info(f"Traitement du lot {i+1}-{batch_end} sur {len(urls_to_process)} URLs...")
        
        # Traiter ce lot en parallèle
        async with aiohttp.ClientSession() as session:
            # Vérifier le statut des URLs cibles pour ce lot
            target_urls_batch = [item["target_absolute"] for item in current_batch]
            target_status_batch = await asyncio.gather(
                *[check_url_status(url, session) for url in target_urls_batch]
            )
            
            # Mettre à jour les résultats du statut des cibles
            for url, status in zip(target_urls_batch, target_status_batch):
                target_status_results[url] = status
            
            # Tracer les redirections pour chaque URL dans ce lot
            tasks_batch = [process_url_batch(item, session, target_status_results) for item in current_batch]
            batch_results = await asyncio.gather(*tasks_batch)
            
            # Ajouter les résultats de ce lot
            for result in batch_results:
                if result:
                    details.append(result)
                    
                    # Mettre à jour les statistiques
                    if result["status"] == "CORRECT":
                        stats["correct_count"] += 1
                    elif result["status"] == "INCORRECT":
                        stats["incorrect_count"] += 1
                    elif result["status"] == "ERREUR":
                        stats["error_count"] += 1
                        
                    if result["redirections_count"] > 1:
                        stats["multi_redirect_count"] += 1
    
    return details, stats
