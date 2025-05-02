import csv
import io
import logging
from urllib.parse import urljoin
from .url_parser import parser_ligne_flexible

def detect_csv_delimiter(csv_content):
    """Détecte automatiquement le délimiteur d'un fichier CSV."""
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(csv_content[:1024], delimiters=";,|\t")
        logging.info(f"Délimiteur CSV détecté: '{dialect.delimiter}'")
        return dialect
    except Exception as e:
        logging.warning(f"Impossible de détecter automatiquement le délimiteur CSV: {e}. Utilisation du délimiteur par défaut ';'")
        dialect = csv.excel
        dialect.delimiter = ';'
        return dialect

def detect_csv_headers(rows):
    """Détecte si le CSV a des en-têtes."""
    has_headers = False
    
    if len(rows) > 0:
        potential_headers = rows[0]
        # Vérifier si la première ligne contient des mots-clés d'en-tête
        header_keywords = ['url', 'source', 'target', 'cible', 'destination', 'final']
        if any(keyword.lower() in col.lower() for col in potential_headers for keyword in header_keywords):
            has_headers = True
            logging.info(f"En-têtes détectés dans le CSV: {potential_headers}")
            rows = rows[1:]  # Ignorer la ligne d'en-têtes
    
    return has_headers, rows

def parse_csv_to_urls(csv_content, domain_prefix=""):
    """
    Parse un contenu CSV et extrait les URLs à traiter.
    
    Args:
        csv_content (str): Contenu du fichier CSV
        domain_prefix (str): Préfixe de domaine pour les URLs relatives
        
    Returns:
        tuple: (urls_to_process, has_headers, total_rows)
    """
    # Détecter le délimiteur
    dialect = detect_csv_delimiter(csv_content)
    
    # Lire le CSV avec le délimiteur détecté
    reader = csv.reader(io.StringIO(csv_content), dialect)
    rows = list(reader)
    
    # Vérifier si le CSV a des en-têtes
    has_headers, rows = detect_csv_headers(rows)
    
    # Mettre à jour le nombre total de lignes à traiter
    total_rows = len(rows)
    logging.info(f"Traitement de {total_rows} lignes de données CSV{' (en-têtes ignorés)' if has_headers else ''}.")
    
    if total_rows == 0:
        return [], has_headers, 0
    
    # Préparer les URLs à traiter
    urls_to_process = []
    
    # Traiter les lignes du CSV en utilisant le parser flexible
    for j, row in enumerate(rows):
        display_line_num = j + 1 + (1 if has_headers else 0)
        
        # Utiliser le parser flexible pour extraire les URLs
        result = parser_ligne_flexible(row, display_line_num)
        if not result:
            continue
            
        source_url, target_url, final_url = result
        
        # Logguer les URLs extraites pour traçabilité
        logging.debug(f"Ligne {display_line_num} - URLs injectées: source={source_url}, cible={target_url}, finale={final_url or 'Non spécifiée'}")
        
        # Construire les URLs absolues si nécessaire
        source_url_absolute = source_url
        if not source_url.startswith(('http://', 'https://')) and domain_prefix:
            if source_url.startswith('/'):
                source_url_absolute = urljoin(domain_prefix, source_url)
            else:
                source_url_absolute = urljoin(f"{domain_prefix}/", source_url)
        
        target_url_absolute = target_url
        if not target_url.startswith(('http://', 'https://')) and domain_prefix:
            if target_url.startswith('/'):
                target_url_absolute = urljoin(domain_prefix, target_url)
            else:
                target_url_absolute = urljoin(f"{domain_prefix}/", target_url)
        
        # Ajouter à la liste des URLs à traiter
        urls_to_process.append({
            "line_num": display_line_num,
            "source": source_url,
            "target": target_url,
            "final": final_url or "",  # Ajouter le champ final_url
            "source_absolute": source_url_absolute,
            "target_absolute": target_url_absolute
        })
    
    return urls_to_process, has_headers, total_rows
