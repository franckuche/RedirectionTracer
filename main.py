import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt

from app.logger import setup_logging
# Importation des routes principales
from app.web_routes import router as web_router
from app.api import router as api_router
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.utils.security import SECRET_KEY, ALGORITHM, get_current_user
from app.database import Base, engine

# Configuration du logging
logger, frontend_logger = setup_logging()

# Configuration des templates
templates = Jinja2Templates(directory="templates")

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

# Création des tables dans la base de données
# Commentez cette ligne en production et utilisez Alembic pour les migrations
Base.metadata.create_all(bind=engine)

# Importer le middleware d'authentification
from app.middleware import auth_middleware

# Ajouter le middleware d'authentification
@app.middleware("http")
async def authenticate_middleware(request: Request, call_next):
    return await auth_middleware(request, call_next)

# Routes simplifiées pour l'authentification
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# Inclusion des routes
app.include_router(web_router)
app.include_router(api_router, prefix="/api")
app.include_router(auth_router, prefix="/api/auth")
app.include_router(admin_router, prefix="/api/admin")

# Point d'entrée pour exécuter l'application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
