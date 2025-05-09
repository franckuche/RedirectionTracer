from fastapi import Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from jose import JWTError, jwt

from .utils.security import SECRET_KEY, ALGORITHM

# Fonction d'aide pour rediriger vers la page de connexion
def redirect_to_login(request_path: str):
    """
    Redirige vers la page de connexion.
    Ne pas ajouter le paramètre redirect si la redirection est vers la page d'accueil.
    """
    import logging
    
    if request_path == "/":
        logging.info(f"Redirection vers la page de connexion (depuis la page d'accueil)")
        return RedirectResponse(url="/login", status_code=303)
    else:
        redirect_url = f"/login?redirect={request_path}"
        logging.info(f"Redirection vers la page de connexion: {redirect_url} (depuis {request_path})")
        return RedirectResponse(url=redirect_url, status_code=303)

# Liste des chemins qui ne nécessitent pas d'authentification
PUBLIC_PATHS = [
    "/static", "/login", "/register",
    "/api/auth/token", "/api/auth/register"
]

def is_public_path(path: str):
    return any(path.startswith(public_path) for public_path in PUBLIC_PATHS)

async def auth_middleware(request: Request, call_next):
    """Middleware pour vérifier l'authentification de l'utilisateur"""
    import logging
    
    path = request.url.path
    
    # Vérifier si le chemin est public
    if is_public_path(path):
        logging.debug(f"Requête vers {path} - Public: True")
        logging.debug(f"Chemin public: {path} - Aucune authentification requise")
        response = await call_next(request)
        return response
        
    # Vérifier si c'est une requête POST avec un token d'authentification dans le formulaire
    if request.method == "POST":
        try:
            # Essayer de récupérer les données du formulaire
            form_data = await request.form()
            auth_token = form_data.get("auth_token")
            post_login_redirect = form_data.get("post_login_redirect")
            
            if auth_token and post_login_redirect == "true":
                logging.debug(f"Requête POST avec token d'authentification pour {path}")
                # Ajouter le token aux en-têtes pour cette requête
                request.headers.__dict__["_list"].append((b"authorization", f"Bearer {auth_token}".encode()))
                response = await call_next(request)
                return response
        except Exception as e:
            logging.error(f"Erreur lors de la lecture des données du formulaire: {e}")
            # Continuer avec la vérification normale
    
    # Vérifier le token d'authentification
    auth_header = request.headers.get("Authorization")
    logging.debug(f"En-tête d'authentification pour {path}: {auth_header and 'Présent' or 'Absent'}")
    
    # Afficher tous les en-têtes pour le débogage
    logging.debug(f"En-têtes de la requête pour {path}: {dict(request.headers)}")
    
    # Vérifier également les cookies pour le token
    auth_cookie = request.cookies.get("access_token")
    logging.debug(f"Cookie d'authentification pour {path}: {auth_cookie and 'Présent' or 'Absent'}")
    
    # Utiliser le token du cookie si l'en-tête d'autorisation n'est pas présent
    if auth_cookie and (not auth_header or not auth_header.startswith("Bearer ")):
        auth_header = f"Bearer {auth_cookie}"
        logging.debug(f"Utilisation du token depuis le cookie pour {path}")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        # Pas de token, rediriger vers la page de connexion pour les routes HTML
        if path.startswith("/api"):
            # Pour les API, renvoyer une erreur 401
            logging.warning(f"Accès API non authentifié refusé: {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Non authentifié"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            # Pour les pages HTML, rediriger vers la page de connexion
            return redirect_to_login(path)
    
    # Extraire et vérifier le token
    token = auth_header.replace("Bearer ", "")
    try:
        # Vérifier le token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        logging.debug(f"Token valide pour l'utilisateur: {email}")
        if email is None:
            logging.warning("Token sans sujet (sub) valide")
            raise JWTError
    except JWTError:
        # Token invalide
        if path.startswith("/api"):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token invalide"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        else:
            # Pour les routes HTML, rediriger vers la page de connexion
            return redirect_to_login(path)
    
    # Token valide, continuer
    logging.info(f"Utilisateur {email} authentifié avec succès pour accéder à {path}")
    response = await call_next(request)
    return response
