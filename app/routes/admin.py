from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from ..database import get_db
from ..models.auth import User
from ..schemas.auth import User as UserSchema
from ..utils.security import get_current_admin_user

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    responses={401: {"description": "Non autorisé"}}
)

@router.get("/users", response_model=List[UserSchema])
async def get_users(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Récupère la liste de tous les utilisateurs (admin uniquement)"""
    users = db.query(User).all()
    return users

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int, 
    status: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_admin_user)
):
    """Met à jour le statut actif/inactif d'un utilisateur (admin uniquement)"""
    # Vérifier que l'utilisateur existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Empêcher un admin de se désactiver lui-même
    if user.id == current_user.id and not status.get("is_active", True):
        raise HTTPException(
            status_code=400, 
            detail="Vous ne pouvez pas désactiver votre propre compte"
        )
    
    # Mettre à jour le statut
    user.is_active = status.get("is_active", user.is_active)
    db.commit()
    
    return {"status": "success", "message": "Statut mis à jour"}

@router.put("/users/{user_id}/admin")
async def update_admin_status(
    user_id: int, 
    status: dict, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_admin_user)
):
    """Met à jour le statut administrateur d'un utilisateur (admin uniquement)"""
    # Vérifier que l'utilisateur existe
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    # Empêcher un admin de se retirer ses propres droits d'admin
    if user.id == current_user.id and not status.get("is_admin", True):
        raise HTTPException(
            status_code=400, 
            detail="Vous ne pouvez pas retirer vos propres droits d'administrateur"
        )
    
    # S'assurer qu'il y a toujours au moins un administrateur
    if not status.get("is_admin", user.is_admin):
        admin_count = db.query(User).filter(User.is_admin == True, User.id != user_id).count()
        if admin_count == 0:
            raise HTTPException(
                status_code=400, 
                detail="Il doit y avoir au moins un administrateur dans le système"
            )
    
    # Mettre à jour le statut
    user.is_admin = status.get("is_admin", user.is_admin)
    db.commit()
    
    return {"status": "success", "message": "Statut administrateur mis à jour"}

@router.get("/stats")
async def get_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_admin_user)):
    """Récupère les statistiques générales (admin uniquement)"""
    # Nombre total d'utilisateurs
    total_users = db.query(User).count()
    
    # Nombre d'utilisateurs actifs
    active_users = db.query(User).filter(User.is_active == True).count()
    
    # Nombre d'administrateurs
    admin_users = db.query(User).filter(User.is_admin == True).count()
    
    # Utilisateurs créés aujourd'hui
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    users_today = db.query(User).filter(
        User.created_at >= today_start,
        User.created_at <= today_end
    ).count()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "users_today": users_today
    }
