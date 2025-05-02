import logging
from typing import Dict, List

def get_modern_browser_headers():
    """Retourne des headers HTTP qui simulent un navigateur moderne (Chrome sur macOS).
    
    Returns:
        dict: Headers HTTP pour simuler un navigateur moderne.
    """
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'fr,fr-FR;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0'
    }

class ProgressFilter(logging.Filter):
    def filter(self, record):
        # Accepter uniquement les logs contenant 'Progression' ou quelques autres mots clés importants
        progress_keywords = ['Progression', 'Début de', 'terminée', 'traitées', 'Traitement du lot', 'Analyse HTTP']
        return any(keyword in record.getMessage() for keyword in progress_keywords)

def calculate_stats(data) -> Dict:
    """Calcule les statistiques à partir des détails d'analyse ou met à jour un dictionnaire de statistiques existant.
    
    Args:
        data: Peut être soit une liste de détails d'analyse, soit un dictionnaire de statistiques existant
        
    Returns:
        Dict: Dictionnaire de statistiques mis à jour
    """
    # Vérifier si data est déjà un dictionnaire de statistiques
    if isinstance(data, dict) and all(key in data for key in ["total", "correct_count", "incorrect_count", "error_count", "multi_redirect_count"]):
        # C'est déjà un dictionnaire de statistiques, calculer les pourcentages
        stats = data
    else:
        # C'est une liste de détails, calculer les statistiques
        details = data
        stats = {
            "total": len(details),
            "correct_count": 0,
            "incorrect_count": 0,
            "error_count": 0,
            "multi_redirect_count": 0
        }
        
        for detail in details:
            if isinstance(detail, dict):
                if detail.get("status") == "CORRECT":
                    stats["correct_count"] += 1
                elif detail.get("status") == "INCORRECT":
                    stats["incorrect_count"] += 1
                elif detail.get("status") == "ERREUR":
                    stats["error_count"] += 1
                
                if detail.get("redirections_count", 0) > 1:
                    stats["multi_redirect_count"] += 1
    
    # Ajouter les pourcentages
    total = stats["total"]
    if total > 0:
        stats["correct_percent"] = round((stats["correct_count"] / total) * 100, 1)
        stats["incorrect_percent"] = round((stats["incorrect_count"] / total) * 100, 1)
        stats["error_percent"] = round((stats["error_count"] / total) * 100, 1)
        stats["multi_redirect_percent"] = round((stats["multi_redirect_count"] / total) * 100, 1)
    else:
        stats["correct_percent"] = 0
        stats["incorrect_percent"] = 0
        stats["error_percent"] = 0
        stats["multi_redirect_percent"] = 0
    
    return stats
