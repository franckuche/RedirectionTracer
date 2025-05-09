"""
Utilitaires pour le calcul de statistiques
"""

def calculate_stats(results):
    """
    Calcule les statistiques à partir des résultats d'analyse de redirections.
    
    Args:
        results (list): Liste des résultats d'analyse de redirections
        
    Returns:
        dict: Dictionnaire contenant les statistiques calculées
    """
    total = len(results)
    if total == 0:
        return {
            "total": 0,
            "correct": 0,
            "incorrect": 0,
            "error": 0,
            "multiple": 0,
            "correct_percent": 0,
            "incorrect_percent": 0,
            "error_percent": 0,
            "multiple_percent": 0,
            "http_codes": {}
        }
    
    # Initialiser les compteurs
    stats = {
        "total": total,
        "correct": 0,
        "incorrect": 0,
        "error": 0,
        "multiple": 0,
        "http_codes": {}
    }
    
    # Compter les différents types de résultats
    for result in results:
        # Compter par statut
        if result.status == "correct":
            stats["correct"] += 1
        elif result.status == "incorrect":
            stats["incorrect"] += 1
        elif result.status == "error":
            stats["error"] += 1
        elif result.status == "multiple":
            stats["multiple"] += 1
        
        # Compter par code HTTP
        http_code = result.http_status
        if http_code:
            if http_code in stats["http_codes"]:
                stats["http_codes"][http_code] += 1
            else:
                stats["http_codes"][http_code] = 1
    
    # Calculer les pourcentages
    stats["correct_percent"] = round((stats["correct"] / total) * 100, 1)
    stats["incorrect_percent"] = round((stats["incorrect"] / total) * 100, 1)
    stats["error_percent"] = round((stats["error"] / total) * 100, 1)
    stats["multiple_percent"] = round((stats["multiple"] / total) * 100, 1)
    
    # Trier les codes HTTP par fréquence
    stats["http_codes"] = dict(sorted(
        stats["http_codes"].items(), 
        key=lambda item: item[1], 
        reverse=True
    ))
    
    return stats
