
from api.v1.endpoints import ai_service, management, vision_service
from fastapi import APIRouter
import core.database as storage

api_router = APIRouter()


data = storage.ia_usage()
if not isinstance(data, list):
    data = []
storage.ia_usage(data)

api_router.include_router(ai_service.router, prefix="/ollama", tags=["OLLAMA - AI Delivery Service"])
api_router.include_router(management.router, prefix="/admin", tags=["ADM - AI Delivery Service"])
api_router.include_router(vision_service.router, prefix="/vision", tags=["VISION - AI Delivery Service"])


