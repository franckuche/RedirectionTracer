import logging
import traceback
from .csv_processor import parse_csv_to_urls
from .url_processor import process_urls_in_batches
from .utils import calculate_stats

# Stockage des tâches en cours (dans une vraie application, utilisez une base de données)
tasks = {}

async def process_csv_task(task_id: str):
    """Traite une tâche d'analyse de fichier CSV."""
    try:
        # Récupérer les données de la tâche
        task_data = tasks[task_id]
        csv_content = task_data["csv_content"]
        domain_prefix = task_data.get("domain_prefix", "")
        
        # Mettre à jour le statut pour indiquer que le traitement a commencé
        tasks[task_id]["status"] = "processing"
        tasks[task_id]["message"] = "Analyse des redirections en cours..."
        tasks[task_id]["progress"] = 0.01  # Démarrer à 1% pour montrer que ça a commencé
        
        # Parser le CSV et extraire les URLs
        urls_to_process, has_headers, total_rows = parse_csv_to_urls(csv_content, domain_prefix)
        
        # Vérifier si des URLs ont été trouvées
        if not urls_to_process:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["message"] = "Aucune URL valide à traiter dans le CSV."
            tasks[task_id]["progress"] = 1.0
            tasks[task_id]["stats"] = {
                "total": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "error_count": 0,
                "multi_redirect_count": 0
            }
            tasks[task_id]["details"] = []
            return
        
        # Traiter les URLs par lots
        details, stats = await process_urls_in_batches(urls_to_process, task_id, tasks)
        
        # Calculer les statistiques finales
        stats = calculate_stats(stats)
        
        # Mettre à jour le statut pour indiquer que le traitement est terminé
        tasks[task_id]["status"] = "completed"
        tasks[task_id]["message"] = "Analyse terminée avec succès."
        tasks[task_id]["progress"] = 1.0
        tasks[task_id]["stats"] = stats
        tasks[task_id]["details"] = details
        
    except Exception as e:
        error_details = traceback.format_exc()
        logging.error(f"Erreur lors du traitement du CSV: {e}")
        logging.error(f"Détails de l'erreur: {error_details}")
        tasks[task_id]["status"] = "error"
        tasks[task_id]["message"] = f"Erreur: {str(e)}"
        tasks[task_id]["progress"] = 0.0

def get_task_status(task_id):
    """Récupère le statut d'une tâche."""
    if task_id not in tasks:
        return None
    
    task_data = tasks[task_id]
    return {
        "status": task_data["status"],
        "message": task_data["message"],
        "progress": task_data["progress"]
    }

def get_task_results(task_id):
    """Récupère les résultats d'une tâche."""
    if task_id not in tasks:
        return None
    
    task_data = tasks[task_id]
    if task_data["status"] != "completed":
        return None
    
    return {
        "stats": task_data["stats"],
        "details": task_data["details"]
    }

def create_task(csv_content, domain_prefix=""):
    """Crée une nouvelle tâche."""
    task_id = __import__('uuid').uuid4().hex
    
    tasks[task_id] = {
        "status": "pending",
        "message": "En attente de traitement...",
        "progress": 0.0,
        "csv_content": csv_content,
        "domain_prefix": domain_prefix,
        "stats": None,
        "details": None
    }
    
    return task_id
