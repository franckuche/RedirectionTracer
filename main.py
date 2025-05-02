import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.logger import setup_logging
from app.routes import router as web_router
from app.api import router as api_router

# Configuration du logging
logger, frontend_logger = setup_logging()

# Création de l'application FastAPI
app = FastAPI(
    title="RedirectionTracer API", 
    description="API pour analyser les redirections d'URLs",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les origines exactes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montage des fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Inclusion des routes
app.include_router(web_router)
app.include_router(api_router, prefix="/api")

# Point d'entrée pour exécuter l'application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
