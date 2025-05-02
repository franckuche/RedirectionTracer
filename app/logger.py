import logging
import os
from .utils import ProgressFilter

def setup_logging(log_file='app.log'):
    """Configure le système de logging de l'application"""
    # Configurer le logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Formatter pour les logs
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Handler pour la console (logs de progression uniquement)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.addFilter(ProgressFilter())  # Ajouter le filtre pour n'afficher que les logs de progression
    root_logger.addHandler(console_handler)
    
    # Handler pour le fichier (tous les logs)
    try:
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
        logging.info(f"Logs détaillés écrits dans {os.path.abspath(log_file)}")
    except Exception as e:
        logging.warning(f"Impossible d'écrire les logs dans {log_file}: {e}")
    
    # Logger spécifique pour ce module
    logger = logging.getLogger(__name__)
    
    # Logger spécifique pour les logs frontend
    frontend_logger = logging.getLogger("frontend")
    frontend_logger.setLevel(logging.INFO)
    
    return logger, frontend_logger
