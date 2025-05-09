# Ce fichier permet à Python de reconnaître le dossier models comme un package

# Exposer les modèles de redirection
from .redirection import (
    FrontendLog,
    TaskStatus,
    UploadResponse,
    RedirectionResult,
    RedirectionStats,
    RedirectionResponse
)

# Exposer les modèles d'authentification
from .auth import User
