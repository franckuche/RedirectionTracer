from fastapi import APIRouter, Request, File, Form, UploadFile, BackgroundTasks, HTTPException, Depends
from typing import Optional, List, Dict, Any
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
import os
import csv
import io

from .task_manager import tasks, get_task_results
from .models import RedirectionResult
from .models.auth import User
from .utils.security import get_current_active_user, get_current_user

# Créer le router pour les routes web
router = APIRouter()

# Configuration des templates
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Page d'accueil de l'application."""
    # Obtenir l'utilisateur actuel en passant l'objet request
    try:
        current_user = await get_current_active_user(request)
    except HTTPException:
        current_user = None
    return templates.TemplateResponse("index.html", {"request": request, "user": current_user})

@router.get("/vue")
async def read_vue(request: Request):
    """Route legacy pour la compatibilité - redirige vers la racine."""
    return RedirectResponse(url="/", status_code=303)

@router.get("/results/{task_id}", response_class=HTMLResponse)
async def show_results(request: Request, task_id: str, current_user: User = Depends(get_current_active_user)):
    """Rendu de la page de résultats"""
    # Vérifier si la tâche existe
    if task_id not in tasks:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Tâche non trouvée",
            "details": f"La tâche avec l'ID {task_id} n'existe pas."
        })
    
    # Vérifier si la tâche est terminée
    task_info = tasks[task_id]
    if task_info["status"] != "completed":
        # Rediriger vers la page d'accueil avec un message d'erreur
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "La tâche n'est pas encore terminée"
        })
    
    # Récupérer les résultats
    stats = task_info.get("stats", {})
    details = task_info.get("details", [])
    
    if not stats or not details:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Résultats incomplets",
            "details": f"Les résultats de la tâche {task_id} sont incomplets ou corrompus."
        })
    
    # Préparer les données pour le template resultats.html
    stats_data = {
        "filename": task_info.get("filename", ""),
        "total": stats.get("total", 0),
        "correct_count": stats.get("correct_count", 0),
        "incorrect_count": stats.get("incorrect_count", 0),
        "error_count": stats.get("error_count", 0),
        "multi_redirect_count": stats.get("multi_redirect_count", 0)
    }
    
    # Convertir les dictionnaires en objets RedirectionResult pour que Jinja puisse accéder aux attributs via detail.final
    details_list = [RedirectionResult(**d) for d in details]
    
    # Trier explicitement par line_num pour garantir l'ordre d'affichage
    details_list = sorted(details_list, key=lambda x: x.line_num)
    
    # Rendre le template avec les résultats
    return templates.TemplateResponse("results_htmx.html", {
        "request": request,
        "task_id": task_id,
        "stats": stats_data,
        "details": details_list
    })

@router.post("/upload", response_class=HTMLResponse)
async def upload_file_htmx(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...), domain_prefix: str = Form("")):
    # Vérifier l'authentification de l'utilisateur
    try:
        from .utils.security import get_current_active_user
        current_user = await get_current_active_user(request)
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Authentification requise",
            "details": "Vous devez être connecté pour effectuer cette action."
        })
    """Endpoint d'upload pour HTMX"""
    try:
        # Traiter le fichier directement sans passer par l'API JSON
        # Vérifier l'extension du fichier
        if not file.filename.endswith('.csv'):
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Format de fichier invalide",
                "details": "Veuillez télécharger un fichier CSV."
            })
        
        # Créer un ID unique pour cette tâche
        import uuid
        task_id = str(uuid.uuid4())
        
        # Lire le contenu du fichier
        contents = await file.read()
        try:
            text = contents.decode('utf-8')
        except UnicodeDecodeError:
            # Si UTF-8 échoue, essayer avec ISO-8859-1 (latin1)
            text = contents.decode('iso-8859-1')
        
        # Stocker les informations de la tâche
        tasks[task_id] = {
            "status": "pending",
            "progress": 0.0,
            "filename": file.filename,
            "domain_prefix": domain_prefix,
            "csv_content": text,
            "result": None
        }
        
        # Démarrer la tâche d'analyse en arrière-plan
        from .api import process_csv_task
        background_tasks.add_task(process_csv_task, task_id)
        
        # Attendre un court instant pour permettre au traitement de démarrer
        import asyncio
        await asyncio.sleep(0.5)
        
        # Renvoyer directement le template de progression
        return templates.TemplateResponse("progress.html", {
            "request": request,
            "task_id": task_id,
            "status": "processing",
            "progress": 0.01,
            "message": "Traitement en cours..."
        })
    
    except Exception as e:
        # En cas d'erreur, renvoyer un message d'erreur
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Erreur lors du traitement du fichier",
            "details": str(e)
        })

@router.get("/api/task/{task_id}/status", response_class=HTMLResponse)
async def check_task_status(request: Request, task_id: str):
    """Vérifier l'état d'une tâche pour HTMX"""
    # Vérifier si la tâche existe
    if task_id not in tasks:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Tâche non trouvée",
            "details": f"La tâche avec l'ID {task_id} n'existe pas."
        })
    
    # Récupérer les informations de la tâche
    task_info = tasks[task_id]
    status = task_info["status"]
    progress = task_info["progress"]
    message = task_info.get("message", "")
    
    # Si la tâche est terminée, forcer une redirection vers la page des résultats
    if status == "completed":
        response = templates.TemplateResponse("progress.html", {
            "request": request,
            "task_id": task_id,
            "status": status,
            "progress": 1.0,
            "message": "Analyse terminée. Redirection vers les résultats..."
        })
        # Ajouter l'en-tête HX-Redirect pour forcer une redirection complète
        response.headers["HX-Redirect"] = f"/results/{task_id}"
        return response
    
    # Si la tâche a échoué, renvoyer une erreur
    if status == "failed":
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Erreur lors de l'analyse",
            "details": message or "Une erreur s'est produite lors de l'analyse des redirections."
        })
    
    # Sinon, renvoyer la progression
    return templates.TemplateResponse("progress.html", {
        "request": request,
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "message": message
    })

@router.get("/api/task/{task_id}/filter", response_class=HTMLResponse)
async def filter_results(request: Request, task_id: str, status: str = "all", http_code: Optional[str] = None, current_user: User = Depends(get_current_active_user)):
    # Log de débogage - entrée de la fonction
    print(f"DEBUG - filter_results - task_id: {task_id}, status: {status}, http_code: {http_code}")
    
    # Vérifier si la tâche existe
    if task_id not in tasks:
        print(f"DEBUG - filter_results - Tâche non trouvée: {task_id}")
        return HTMLResponse(
            content="<tr><td colspan='6' class='px-6 py-8 text-center text-danger-500 border-b border-secondary-200'>"
            "<p class='text-lg font-medium'>Tâche non trouvée</p></td></tr>"
        )
    
    # Vérifier si la tâche est terminée
    task_info = tasks[task_id]
    print(f"DEBUG - filter_results - Status de la tâche: {task_info['status']}")
    
    if task_info["status"] != "completed":
        return HTMLResponse(
            content="<tr><td colspan='6' class='px-6 py-8 text-center text-warning-500 border-b border-secondary-200'>"
            "<p class='text-lg font-medium'>Traitement en cours...</p></td></tr>"
        )
    
    # Récupérer les résultats
    # Vérifier si les résultats sont dans task_info["result"] ou directement dans task_info
    if "result" in task_info and task_info["result"] is not None:
        results = task_info["result"]
    else:
        # Utiliser les détails directement depuis task_info
        results = task_info
    
    # Vérifier si details existe et n'est pas None
    if not hasattr(results, "details") or results.details is None:
        if "details" in task_info:
            # Convertir les dictionnaires en objets RedirectionResult
            details_list = [RedirectionResult(**d) for d in task_info["details"]]
            
            # Trier explicitement par line_num pour garantir l'ordre d'affichage
            details_list = sorted(details_list, key=lambda x: x.line_num)
            
            # Créer un objet dynamique pour stocker les détails
            from types import SimpleNamespace
            results = SimpleNamespace(details=details_list)
        else:
            print(f"DEBUG - filter_results - Pas de détails trouvés dans la tâche")
            return HTMLResponse(
                content="<tr><td colspan='6' class='px-6 py-8 text-center text-danger-500 border-b border-secondary-200'>"
                "<p class='text-lg font-medium'>Résultats non disponibles</p></td></tr>"
            )
    
    print(f"DEBUG - filter_results - Nombre total de résultats: {len(results.details)}")
    
    # Filtrer les résultats en fonction du statut et du code HTTP
    filtered_details = []
    
    for detail in results.details:
        # Filtre par statut
        status_match = status.lower() == "all" or detail.status == status.upper()
        
        # Filtre par code HTTP
        http_code_match = http_code is None or http_code.lower() == "all" or str(detail.http_status) == http_code
        
        # Log de débogage pour chaque détail
        print(f"DEBUG - filter_results - Détail: status={detail.status}, http_status={detail.http_status}, status_match={status_match}, http_code_match={http_code_match}")
        
        # Appliquer les deux filtres (ET logique)
        if status_match and http_code_match:
            # Utiliser line_num s'il est disponible, sinon utiliser line
            line_value = getattr(detail, "line_num", getattr(detail, "line", 0))
            
            detail_dict = {
                "line_num": line_value,
                "source": detail.source,
                "target": detail.target,
                "final": detail.final,
                "http_status": detail.http_status,
                "conclusion": detail.conclusion,
                "status": detail.status,
                "redirects": getattr(detail, "redirections_count", 0)
            }
            filtered_details.append(detail_dict)
            print(f"DEBUG - filter_results - Détail ajouté aux résultats filtrés: {detail_dict}")
    
    # Utiliser une variable globale pour stocker les filtres
    global _filters
    if '_filters' not in globals():
        global _filters
        _filters = {}
    
    _filters[task_id] = {
        "status": status,
        "http_code": http_code
    }
    
    # Nombre de résultats filtrés pour référence
    filtered_count = len(filtered_details)
    
    try:
        # Trier les résultats filtrés par line_num pour garantir l'ordre d'affichage
        filtered_details = sorted(filtered_details, key=lambda x: x["line_num"])
        
        # Rendre le template partiel avec uniquement les lignes du tableau
        response = templates.TemplateResponse(
            "partials/results_table_body.html",
            {"request": request, "details": filtered_details}
        )
        print(f"DEBUG - filter_results - Template rendu avec succès")
        return response
    except Exception as e:
        print(f"ERREUR - filter_results - Exception lors du rendu du template: {str(e)}")
        import traceback
        print(traceback.format_exc())
    task_info = tasks[task_id]
    if task_info["status"] != "completed":
        raise HTTPException(status_code=400, detail="La tâche n'est pas terminée")
    
    results = task_info["result"]
    
    # Créer un fichier CSV en mémoire
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Écrire l'en-tête
    writer.writerow(["Ligne", "URL Source", "URL Cible", "URL Finale", "Statut HTTP", "Redirections", "Statut", "Conclusion"])
    
    # Filtrer les résultats si demandé
    details_to_export = results.details
    filename_suffix = "complet"
    
    if filtered and '_filters' in globals() and task_id in _filters:
        # Récupérer les filtres actuels
        current_filters = _filters[task_id]
        status_filter = current_filters.get("status")
        http_code_filter = current_filters.get("http_code")
        
        # Appliquer les filtres
        filtered_details = []
        for detail in details_to_export:
            status_match = status_filter.lower() == "all" or detail.status == status_filter.upper()
            http_code_match = http_code_filter is None or http_code_filter.lower() == "all" or str(detail.http_status) == http_code_filter
            
            if status_match and http_code_match:
                filtered_details.append(detail)
        
        details_to_export = filtered_details
        
        # Construire un suffixe de nom de fichier basé sur les filtres
        filter_parts = []
        if status_filter and status_filter.lower() != "all":
            filter_parts.append(f"status-{status_filter.lower()}")
        if http_code_filter and http_code_filter.lower() != "all":
            filter_parts.append(f"http-{http_code_filter}")
        
        if filter_parts:
            filename_suffix = "_".join(filter_parts)
        else:
            filename_suffix = "filtre"
    
    # Écrire les données
    for detail in details_to_export:
        writer.writerow([
            detail.line,
            detail.source,
            detail.target,
            detail.final,
            detail.http_status,
            detail.redirections_count,
            detail.status,
            detail.conclusion
        ])
    
    # Préparer la réponse
    output.seek(0)
    headers = {
        'Content-Disposition': f'attachment; filename="resultats_{task_id}_{filename_suffix}.csv"'
    }
    return Response(content=output.getvalue(), media_type="text/csv", headers=headers)

@router.get("/api/task/{task_id}/download-filtered")
async def download_filtered_results(task_id: str, current_user: User = Depends(get_current_active_user)):
    """Télécharger les résultats filtrés d'une tâche au format CSV"""
    return await download_results(task_id, filtered=True)
