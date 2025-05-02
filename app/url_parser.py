import re
import logging
from urllib.parse import urlparse

def est_url_valide(url):
    """Vérifie si une URL est valide en vérifiant sa structure."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception as e:
        logging.warning(f"URL invalide: {url}, erreur: {e}")
        return False

def extraire_urls_utiles(texte):
    """Extrait toutes les URLs valides d'un texte et élimine les doublons."""
    # Vérifier que le texte est bien une chaîne de caractères
    if not isinstance(texte, str):
        texte = str(texte)
        
    # Expression régulière améliorée pour capturer les URLs
    urls = re.findall(r'https?://[^\s"\'<>]+', texte)
    
    # Nettoyer les URLs (enlever les caractères de ponctuation à la fin)
    urls = [url.rstrip('.,;:"') for url in urls]
    
    # Éliminer les doublons tout en préservant l'ordre
    uniques = list(dict.fromkeys(urls))
    
    # Filtrer les URLs valides
    valides = [url for url in uniques if est_url_valide(url)]
    
    return valides

def parser_ligne_flexible(row, ligne_num):
    """
    Analyse une ligne brute du CSV et extrait les URLs source, cible et finale de manière robuste.
    
    Args:
        row: ligne brute du CSV (peut contenir 1 ou plusieurs colonnes)
        ligne_num: numéro de ligne pour le log
        
    Returns:
        tuple: (source_url, target_url, final_url) ou None si pas assez d'URLs valides
    """
    try:
        # Vérifier que row est bien une liste ou un itérable
        if not isinstance(row, (list, tuple)):
            row = [str(row)]
            
        # Fusionner les colonnes en un seul bloc de texte
        texte = " ".join(str(col) for col in row if col)
        
        # Extraire toutes les URLs valides
        urls = extraire_urls_utiles(texte)
        
        if len(urls) < 2:
            logging.warning(f"Ligne {ligne_num}: Pas assez d'URLs valides détectées ({urls})")
            return None
        
        source = urls[0]
        cible = urls[1]
        finale = urls[2] if len(urls) >= 3 else None
        
        logging.info(f"Ligne {ligne_num}: URLs nettoyées - Source: {source} | Cible: {cible} | Finale: {finale or 'Non disponible'}")
        return source, cible, finale
    except Exception as e:
        logging.error(f"Erreur dans parser_ligne_flexible pour la ligne {ligne_num}: {e}")
        return None

def parser_ligne_brute(cells):
    """Analyse une ligne brute du CSV et extrait les URLs source, cible et finale.
    
    Args:
        cells: liste des colonnes CSV brutes (souvent une seule colonne collée)
        
    Returns:
        tuple: (source_url, target_url, final_url)
    """
    # Concaténer toutes les cellules en un seul texte
    texte = " ".join(str(cell) for cell in cells if cell)
    
    # Extraire toutes les URLs valides
    urls = extraire_urls_utiles(texte)
    
    # Attribuer les URLs aux variables correspondantes
    source = urls[0] if len(urls) >= 1 else ""
    cible = urls[1] if len(urls) >= 2 else ""
    finale = urls[2] if len(urls) >= 3 else ""
    
    logging.info(f"URLs extraites: source={source}, cible={cible}, finale={finale}")
    
    return source, cible, finale

def nettoyer_url(url):
    """Nettoie une URL en supprimant les espaces et en ajoutant https:// si nécessaire."""
    if not url:
        return ""
        
    # Supprimer les espaces
    url = url.strip()
    
    # Ajouter https:// si nécessaire
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    return url