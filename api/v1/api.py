
from api.v1.endpoints import ai_service, management, vllm_service
from fastapi import APIRouter
import core.database as storage

api_router = APIRouter()


data = storage.ia_usage()
if not isinstance(data, list):
    data = []
storage.ia_usage(data)

api_router.include_router(ai_service.router, prefix="/ai", tags=["AI Delivery Service"])
api_router.include_router(management.router, prefix="/admin", tags=["AI Delivery Service"])
api_router.include_router(vllm_service.router, prefix="/numind", tags=["AI Delivery Service"])


