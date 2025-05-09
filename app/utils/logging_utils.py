import logging

class ProgressFilter(logging.Filter):
    """Filtre qui ne laisse passer que les logs de progression"""
    
    def filter(self, record):
        # Vérifier si le message contient des indicateurs de progression
        progress_indicators = [
            "Progression", 
            "Traitement", 
            "Analyse", 
            "Terminé",
            "Démarrage",
            "Chargement",
            "Exportation"
        ]
        
        # Vérifier si le message contient l'un des indicateurs
        if record.getMessage():
            for indicator in progress_indicators:
                if indicator in record.getMessage():
                    return True
        
        # Par défaut, ne pas afficher dans la console
        return False
