from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from io import StringIO
import csv
import logging
from urllib.parse import urljoin
import json

# Configuration du logging
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Set level for the logger

# Console Handler (affiche les logs dans le terminal)
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

# File Handler (écrit les logs dans app.log)
file_handler = logging.FileHandler('app.log', encoding='utf-8')
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# Fonction pour tracer une redirection jusqu'à sa fin ou une boucle
def trace_redirection(start_url, redirection_map):
    path = [start_url]
    current_url = start_url
    while True:
        next_url = redirection_map.get(current_url)
        if next_url is None:
            # Plus de redirection connue, c'est la fin
            return current_url
        if next_url in path:
            # Boucle détectée dans cette trace spécifique
            path.append(next_url) # Ajoute pour voir la fermeture de boucle
            # Retourne la boucle détectée pour l'afficher
            loop_start_index = path.index(next_url)
            return f"LOOP: {' -> '.join(path[loop_start_index:])}"
        if len(path) > 50: # Sécurité anti-boucle infinie (si map externe)
            return "ERROR: Chain too long (max 50 hops)"
        path.append(next_url)
        current_url = next_url

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/detect-loops")
async def detect_loops(
    request: Request,
    file: UploadFile = File(...),
    domain_prefix: str = Form(None) # Récupère le préfixe du formulaire
):
    logger.info(f"Fichier reçu: {file.filename}, Type: {file.content_type}")
    if domain_prefix:
        # Nettoyer le préfixe (assurer qu'il se termine par / s'il n'est pas vide)
        domain_prefix = domain_prefix.strip()
        if domain_prefix and not domain_prefix.endswith('/'):
            domain_prefix += '/'
        logger.info(f"Préfixe de domaine fourni: {domain_prefix}")
    else:
        logger.info("Aucun préfixe de domaine fourni.")

    content = await file.read()
    csvfile = StringIO(content.decode('utf-8')) # Assumer UTF-8, ajuster si nécessaire
    reader = csv.DictReader(csvfile)

    redirection_map = {}
    redirection_set = set()
    original_pairs = [] # Pour stocker les paires lues
    row_count = 0

    try:
        for row in reader:
            if "source_url" not in row or "target_url" not in row:
                logger.warning(f"Ligne {row_count + 1} ignorée: manque 'source_url' ou 'target_url'")
                continue
            source = row["source_url"].strip()
            target = row["target_url"].strip()

            # Appliquer le préfixe si l'URL est relative et un préfixe est fourni
            if domain_prefix:
                if not source.startswith(('http://', 'https://')):
                    source = urljoin(domain_prefix, source)
                if not target.startswith(('http://', 'https://')):
                    target = urljoin(domain_prefix, target)

            if not source or not target: # Ignorer les lignes avec des URL vides après nettoyage/prefixage
                 logger.warning(f"Ligne {row_count + 1} ignorée: URL source ou cible vide après traitement.")
                 continue
            redirection_map[source] = target
            redirection_set.add((source, target))
            original_pairs.append({"source": source, "target": target, "line": row_count + 2}) # +2 car header + 0-based index
            row_count += 1
        logger.info(f"{row_count} lignes de redirection lues et chargées.")
    except csv.Error as e:
        logger.error(f"Erreur lors de la lecture du CSV: {e}")
        # Peut-être retourner une page d'erreur ici
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"Erreur CSV: {e}"}, status_code=400)
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la lecture du fichier: {e}")
        return templates.TemplateResponse("error.html", {"request": request, "error_message": f"Erreur Fichier: {e}"}, status_code=500)

    # --- Détection globale des boucles (comme avant) ---
    visited_global = set()
    global_loops = []
    processed_starts = 0
    total_starts = len(redirection_map)

    logger.info(f"Début de la détection GLOBALE des boucles pour {total_starts} points de départ potentiels.")

    for start_url in redirection_map:
        current_path = []
        seen_in_path = set()
        url = start_url

        while url:
            if url in seen_in_path:
                loop_start_index = current_path.index(url)
                loop_path = current_path[loop_start_index:] + [url]
                is_internal = all(
                    (loop_path[i], loop_path[i+1]) in redirection_set
                    for i in range(len(loop_path) - 1)
                )
                global_loops.append({
                    "loop": loop_path,
                    "internal": is_internal
                })
                break
            if url in visited_global:
                break
            seen_in_path.add(url)
            current_path.append(url)
            url = redirection_map.get(url)
        visited_global.update(seen_in_path)
        processed_starts += 1
        if processed_starts % 100 == 0:
            logger.info(f"Progression détection GLOBALE: {processed_starts}/{total_starts} points analysés.")

    logger.info(f"Détection GLOBALE terminée. {len(global_loops)} boucles trouvées.")

    # --- Analyse détaillée de chaque redirection originale ---
    logger.info(f"Début de l'analyse détaillée pour {len(original_pairs)} redirections du fichier.")
    redirection_details = []
    for i, pair in enumerate(original_pairs):
        source_url = pair["source"]
        target_url = pair["target"]
        line_num = pair["line"]

        final_destination = trace_redirection(source_url, redirection_map)

        if final_destination == target_url:
            conclusion = "OK: URL finale correspond à la target du CSV."
        elif isinstance(final_destination, str) and final_destination.startswith("LOOP:"):
            conclusion = f"ERREUR: Boucle détectée ({final_destination[5:]}). Target CSV non atteinte."
        elif isinstance(final_destination, str) and final_destination.startswith("ERROR:"):
             conclusion = f"ERREUR: {final_destination[7:]}"
        else:
            conclusion = f"KO: URL finale ({final_destination}) différente de la target CSV ({target_url})."

        redirection_details.append({
            "line": line_num,
            "source": source_url,
            "target": target_url,
            "final": final_destination if not final_destination.startswith("LOOP:") else "(Boucle détectée)", # Pour l'affichage simple
            "conclusion": conclusion
        })
        if (i + 1) % 100 == 0:
             logger.info(f"Progression analyse détaillée: {i+1}/{len(original_pairs)} lignes traitées.")

    logger.info("Analyse détaillée terminée.")

    # Retourne le template resultats.html avec les deux types de données
    return templates.TemplateResponse(
        "resultats.html",
        {
            "request": request,
            "loops": global_loops, # Renommé pour clarté
            "details": redirection_details, # Nouvelle liste
            "details_json": json.dumps(redirection_details), # Ajout des détails en JSON
            "filename": file.filename,
            "domain_prefix_used": domain_prefix
        }
    )
