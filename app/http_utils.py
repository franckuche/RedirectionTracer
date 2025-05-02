import logging
import requests
import aiohttp
import asyncio
import re
from urllib.parse import urlparse, urljoin
from .utils import get_modern_browser_headers

# Vérifier si Brotli est disponible
BROTLI_AVAILABLE = False
try:
    import brotli
    BROTLI_AVAILABLE = True
    logging.info("Le package 'brotli' est installé et disponible pour la décompression.")
except ImportError:
    logging.warning("Le package 'brotli' n'est pas installé. La décompression brotli ne sera pas disponible.")

async def trace_http_redirection_async(start_url, session, max_redirects=20, timeout=10):
    """Version asynchrone de trace_http_redirection utilisant aiohttp.
    
    Args:
        start_url (str): L'URL de départ.
        session (aiohttp.ClientSession): Session aiohttp à utiliser pour les requêtes.
        max_redirects (int): Nombre maximum de redirections à suivre.
        timeout (int): Timeout en secondes pour chaque requête.
        
    Returns:
        tuple: (final_url: str | None, error: str | None, redirections_count: int, http_status: int)
    """
    logging.info(f"-- Début trace HTTP async pour: {start_url}")
    
    # Utiliser les headers de navigateur moderne
    headers = get_modern_browser_headers()
    
    # Désactiver le suivi automatique des redirections
    try:
        async with session.get(start_url, allow_redirects=False, headers=headers, timeout=timeout) as response:
            status = response.status
            
            # Si pas de redirection, retourner l'URL finale
            if status < 300 or status >= 400:
                logging.info(f"     -> URL finale: {start_url} (code {status})")
                return start_url, None, 0, status
            
            # Suivre les redirections manuellement
            redirect_count = 0
            current_url = start_url
            redirections = []
            
            while status >= 300 and status < 400 and redirect_count < max_redirects:
                redirect_count += 1
                
                # Récupérer l'URL de redirection
                location = response.headers.get('Location', '')
                
                # Construire l'URL absolue si nécessaire
                if not location.startswith(('http://', 'https://')):
                    # Récupérer le domaine de l'URL actuelle
                    parsed_url = urlparse(current_url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    
                    # Si l'URL de redirection commence par '/', c'est une URL absolue par rapport au domaine
                    if location.startswith('/'):
                        next_url = urljoin(base_url, location)
                    else:
                        # Sinon, c'est une URL relative par rapport au chemin actuel
                        path = '/'.join(parsed_url.path.split('/')[:-1]) + '/'
                        next_url = urljoin(f"{base_url}{path}", location)
                else:
                    next_url = location
                
                # Enregistrer cette redirection
                logging.info(f"     -> Redirection {redirect_count}: {current_url} -> {next_url} (code {status})")
                redirections.append((status, current_url, next_url))
                
                # Passer à l'URL suivante
                current_url = next_url
                
                # Faire une nouvelle requête vers l'URL de redirection
                try:
                    async with session.get(next_url, allow_redirects=False, headers=headers, timeout=timeout) as response:
                        status = response.status
                        
                        # Si pas de redirection, on a atteint l'URL finale
                        if status < 300 or status >= 400:
                            break
                except Exception as e:
                    logging.error(f"   -> Erreur lors de la requête vers {next_url}: {e}")
                    return None, f"Erreur lors de la requête vers {next_url}: {e}", redirect_count, 0
            
            # Vérifier si on a atteint la limite de redirections
            if redirect_count >= max_redirects:
                logging.error(f"   -> Trop de redirections (> {max_redirects}) pour {start_url}")
                return None, f"Trop de redirections (> {max_redirects})", redirect_count, 0
            
            # Afficher la chaîne de redirection
            if redirect_count > 0:
                logging.info(f"     -> Chaîne de redirection async ({redirect_count} sauts):")
                for i, (code, from_url, to_url) in enumerate(redirections, 1):
                    logging.info(f"        {i}. {code} {from_url} -> {to_url}")
            
            # Retourner l'URL finale
            logging.info(f"     -> URL finale: {current_url} (code {status})")
            return current_url, None, redirect_count, status
            
    except aiohttp.ClientResponseError as e:
        if hasattr(e, 'history') and len(e.history) > max_redirects:
            logging.error(f"   -> Trop de redirections (> {max_redirects}) pour {start_url}")
            return None, f"Trop de redirections (> {max_redirects})", 0, 0
        else:
            logging.error(f"   -> Erreur: Status HTTP {e.status} pour {start_url}: {e}")
            return None, f"Erreur HTTP {e.status}", 0, e.status
            
    except asyncio.TimeoutError:
        logging.error(f"   -> Erreur: Timeout lors de la requête async vers {start_url}")
        return None, f"Timeout pour {start_url}", 0, 0
        
    except aiohttp.ClientConnectorError as e:
        logging.error(f"   -> Erreur: Problème de connexion async vers {start_url}: {e}")
        return None, f"Erreur de connexion pour {start_url}", 0, 0
        
    except Exception as e:
        error_str = str(e)
        
        # Détection spécifique de l'erreur Brotli
        if "Can not decode content-encoding: brotli (br)" in error_str:
            logging.warning(f"   -> Compression Brotli détectée pour {start_url}")
            
            # Même si Brotli est installé, aiohttp peut parfois avoir des problèmes avec
            # Nous allons considérer que la redirection est réussie si nous pouvons extraire l'URL finale
            url_match = re.search(r"url='([^']+)'$", error_str)
            url = url_match.group(1) if url_match else start_url
            
            # Retourner l'URL extraite comme URL finale
            return url, None, 1, 200  # On considère qu'il y a eu au moins une redirection
        
        logging.error(f"   -> Erreur inattendue lors de la requête async vers {start_url}: {e}")
        return None, f"Erreur: {str(e)}", 0, 0

def trace_http_redirection(start_url, max_redirects=20, timeout=10):
    """Suit la chaîne de redirection HTTP pour une URL donnée en utilisant
    le suivi automatique des redirections de requests.

    Args:
        start_url (str): L'URL de départ.
        max_redirects (int): Nombre maximum de redirections à suivre.
        timeout (int): Timeout en secondes pour chaque requête.

    Returns:
        tuple: (final_url: str | None, error: str | None, redirections_count: int)
               Retourne l'URL finale, un message d'erreur éventuel et le nombre de redirections.
    """
    headers = get_modern_browser_headers()
    
    try:
        # Suivre les redirections automatiquement
        response = requests.get(
            start_url,
            headers=headers,
            allow_redirects=True,
            timeout=timeout,
            max_redirects=max_redirects
        )
        
        # Récupérer l'historique des redirections
        redirections_count = len(response.history)
        
        if redirections_count > 0:
            logging.info(f"Redirection de {start_url} vers {response.url} ({redirections_count} sauts)")
            
        return response.url, None, redirections_count
        
    except requests.exceptions.TooManyRedirects:
        logging.error(f"   -> Trop de redirections (> {max_redirects}) pour {start_url}")
        return None, f"Trop de redirections (> {max_redirects})", 0
        
    except requests.exceptions.Timeout:
        logging.error(f"   -> Erreur: Timeout lors de la requête vers {start_url}")
        return None, f"Timeout pour {start_url}", 0
        
    except requests.exceptions.ConnectionError as e:
        logging.error(f"   -> Erreur: Problème de connexion vers {start_url}: {e}")
        return None, f"Erreur de connexion pour {start_url}", 0
        
    except requests.exceptions.RequestException as e:
        status_code = getattr(e.response, 'status_code', "N/A") if hasattr(e, 'response') else "N/A"
        logging.error(f"   -> Erreur: Requête vers {start_url} échouée: {status_code} - {e}")
        return None, f"Erreur {status_code} pour {start_url}", 0

async def check_url_status(url, session, timeout=10):
    """Vérifie le statut HTTP d'une URL.
    
    Args:
        url (str): L'URL à vérifier.
        session (aiohttp.ClientSession): Session aiohttp à utiliser pour les requêtes.
        timeout (int): Timeout en secondes pour la requête.
        
    Returns:
        int: Le code de statut HTTP ou 0 en cas d'erreur.
    """
    # Utiliser les headers de navigateur moderne
    headers = get_modern_browser_headers()
    
    try:
        async with session.get(url, allow_redirects=True, timeout=timeout) as response:
            return response.status
    except Exception as e:
        logging.error(f"Erreur lors de la vérification du statut de {url}: {e}")
        return 0
