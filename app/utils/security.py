from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os
import secrets
import logging

from ..schemas.auth import TokenData
from ..models.auth import User
from ..database import get_db

# Configuration de sécurité
# Générer une clé secrète forte pour la production
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Configuration du hachage de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Fonctions utilitaires pour la sécurité
def verify_password(plain_password, hashed_password):
    """Vérifie si le mot de passe en clair correspond au mot de passe haché"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Génère un hash sécurisé pour le mot de passe"""
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    """Authentifie un utilisateur par son email et mot de passe"""
    logging.debug(f"Tentative d'authentification pour l'email: {username}")
    
    # Le paramètre username contient en fait l'email (pour compatibilité avec OAuth2PasswordRequestForm)
    user = db.query(User).filter(User.email == username).first()
    
    if not user:
        logging.warning(f"Authentification échouée: utilisateur non trouvé pour l'email {username}")
        return False
    
    if not verify_password(password, user.hashed_password):
        logging.warning(f"Authentification échouée: mot de passe incorrect pour {username}")
        return False
    
    logging.debug(f"Authentification réussie pour {username}")
    
    # Mise à jour de la date de dernière connexion
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Crée un token JWT pour l'authentification"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_token_from_cookie_or_header(request: Request = None):
    """Récupère le token depuis les cookies ou l'en-tête d'autorisation"""
    if request is None:
        # Si request n'est pas fourni, utiliser oauth2_scheme standard
        try:
            return await oauth2_scheme(request)
        except HTTPException:
            # Si l'en-tête d'autorisation n'est pas présent, renvoyer None
            return None
    
    # Vérifier d'abord l'en-tête d'autorisation
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    # Ensuite, vérifier les cookies
    auth_cookie = request.cookies.get("access_token")
    if auth_cookie:
        logging.debug("Token récupéré depuis le cookie")
        return auth_cookie
    
    # Aucun token trouvé
    return None

async def get_current_user(request: Request = None, db: Session = None):
    """Récupère l'utilisateur actuel à partir du token JWT"""
    # Si db n'est pas fourni, l'obtenir via get_db
    if db is None:
        # Obtenir une session de base de données
        from ..database import get_db
        db_generator = get_db()
        db = next(db_generator)
    
    # Récupérer le token depuis les cookies ou l'en-tête
    token = await get_token_from_cookie_or_header(request)
    
    if not token:
        logging.warning("Aucun token d'authentification trouvé")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentification invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logging.debug(f"Vérification du token: {token[:15]}...")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentification invalide",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            logging.warning("Token JWT sans sujet (sub)")
            raise credentials_exception
        
        logging.debug(f"Token décodé avec succès pour l'email: {email}")
        token_data = TokenData(username=email)  # On garde username dans TokenData pour compatibilité
    except JWTError as e:
        logging.error(f"Erreur de décodage du token JWT: {str(e)}")
        raise credentials_exception
    
    user = db.query(User).filter(User.email == token_data.username).first()
    if user is None:
        logging.warning(f"Utilisateur non trouvé pour l'email: {token_data.username}")
        raise credentials_exception
    
    logging.debug(f"Utilisateur authentifié: {user.email}")
    return user

async def get_current_active_user(request: Request = None):
    """Vérifie si l'utilisateur actuel est actif"""
    # Récupérer l'utilisateur courant en passant l'objet request
    current_user = await get_current_user(request)
    
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Utilisateur inactif")
    return current_user

async def get_current_admin_user(request: Request = None):
    """Vérifie si l'utilisateur actuel est un administrateur"""
    # Récupérer l'utilisateur actuel
    current_user = await get_current_active_user(request)
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Droits d'administrateur requis"
        )
    return current_user
