from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from fastapi.templating import Jinja2Templates
import os
import logging

from ..database import get_db
from ..models.auth import User
from ..schemas.auth import UserCreate, Token, User as UserSchema
from ..utils.security import (
    authenticate_user, 
    create_access_token, 
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    get_current_active_user,
    get_current_admin_user
)

router = APIRouter(
    tags=["authentication"],
    responses={401: {"description": "Non autorisé"}}
)

templates = Jinja2Templates(directory="templates")

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Endpoint pour obtenir un token d'authentification"""
    logging.info(f"Tentative de connexion pour l'utilisateur: {form_data.username}")
    
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logging.warning(f"Échec de connexion pour l'utilisateur: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logging.info(f"Connexion réussie pour l'utilisateur: {user.email}")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    # Log pour le débogage du token
    token_preview = access_token[:15] + "..." if access_token else "None"
    logging.info(f"Token généré pour {user.email}: {token_preview}")
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserSchema)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Endpoint pour créer un nouvel utilisateur"""
    logging.info(f"Tentative d'inscription pour l'email: {user.email}")
    
    # Vérifier si l'email existe déjà
    db_user_email = db.query(User).filter(User.email == user.email).first()
    if db_user_email:
        logging.warning(f"Échec d'inscription: email déjà utilisé: {user.email}")
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    
    # Créer un nouvel utilisateur
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        # Le premier utilisateur créé est automatiquement admin si aucun autre utilisateur n'existe
        is_admin=db.query(User).count() == 0
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/me", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Endpoint pour obtenir les informations de l'utilisateur connecté"""
    return current_user

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Page de connexion"""
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Page d'inscription"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """Page d'administration (accessible uniquement aux administrateurs)"""
    # Récupérer l'utilisateur administrateur
    current_user = await get_current_admin_user(request)
    return templates.TemplateResponse("admin.html", {"request": request, "user": current_user})

@router.get("/logout")
async def logout():
    """Déconnexion (côté client via JavaScript)"""
    import logging
    logging.info("Déconnexion de l'utilisateur")
    
    # Créer une réponse de redirection
    response = RedirectResponse(url="/login", status_code=303)
    
    # Supprimer explicitement le cookie d'authentification
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="auth_token")
    response.delete_cookie(key="token")
    response.delete_cookie(key="jwt")
    
    # Ajouter des en-têtes pour éviter la mise en cache
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    
    return response
