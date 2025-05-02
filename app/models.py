from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Modèles Pydantic pour l'API
class FrontendLog(BaseModel):
    level: str = "info"
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

class TaskStatus(BaseModel):
    task_id: str
    status: str  # 'pending', 'completed', 'failed'
    progress: float  # 0.0 à 1.0
    message: Optional[str] = None

class UploadResponse(BaseModel):
    task_id: str
    message: str

class RedirectionResult(BaseModel):
    line_num: int
    source: str
    target: str
    final: str
    redirections_count: int
    status: str
    http_status: int
    target_status: Optional[int] = None
    conclusion: str
    
    # Alias pour la rétrocompatibilité
    @property
    def line(self) -> int:
        return self.line_num

class RedirectionStats(BaseModel):
    total: int
    correct_count: int
    incorrect_count: int
    error_count: int
    multi_redirect_count: int

class RedirectionResponse(BaseModel):
    filename: str
    stats: RedirectionStats
    details: List[RedirectionResult]
