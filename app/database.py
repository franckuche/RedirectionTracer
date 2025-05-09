from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

# Utilisez une variable d'environnement pour la configuration de la base de données
# ou utilisez une valeur par défaut pour le développement
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/redirection_tracer")

# Pour le développement, nous pouvons utiliser SQLite si PostgreSQL n'est pas disponible
if os.getenv("DEV_MODE", "True").lower() == "true" and not os.getenv("DATABASE_URL"):
    logger.info("Mode développement activé, utilisation de SQLite")
    DATABASE_URL = "sqlite:///./redirection_tracer.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Pour PostgreSQL
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency pour l'injection de dépendance dans FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
