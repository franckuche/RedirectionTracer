import logging
from fastapi import APIRouter, File, Form, UploadFile, BackgroundTasks, HTTPException
from typing import Dict, List, Any

from .models import UploadResponse, TaskStatus, RedirectionResponse, FrontendLog
from .task_manager import tasks, process_csv_task, get_task_status, get_task_results, create_task

# Créer le router API
router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file_api(background_tasks: BackgroundTasks, 
                     file: UploadFile = File(...), 
                     domain_prefix: str = Form("")):
    """Upload d'un fichier CSV pour analyse"""
    # Vérifier l'extension du fichier
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Veuillez télécharger un fichier CSV.")
    
    # Lire le contenu du fichier
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    # Créer une nouvelle tâche
    task_id = create_task(csv_content, domain_prefix)
    
    # Démarrer le traitement en arrière-plan
    background_tasks.add_task(process_csv_task, task_id)
    
    return {"task_id": task_id, "message": "Fichier reçu, traitement en cours..."}

@router.get("/task/{task_id}/status", response_model=TaskStatus)
async def get_task_status_api(task_id: str):
    """Récupérer le statut d'une tâche en cours"""
    status = get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Tâche non trouvée.")
    
    return status

@router.get("/task/{task_id}/results", response_model=RedirectionResponse)
async def get_task_results_api(task_id: str):
    """Récupérer les résultats d'une tâche terminée"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Tâche non trouvée.")
    
    results = get_task_results(task_id)
    if not results:
        raise HTTPException(status_code=400, detail="La tâche n'est pas encore terminée.")
    
    return results

@router.post("/logs")
async def log_from_frontend(log_data: FrontendLog):
    """Endpoint pour recevoir les logs du frontend"""
    logging.info(f"[FRONTEND] {log_data.message}")
    return {"status": "success"}
