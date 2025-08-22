

from fastapi import APIRouter
import core.database as storage
from schema.log_schema import LogEntry




router = APIRouter()


from typing import List

@router.get("/dashboard", response_model=List[LogEntry])
async def get_logs():
    data = storage.ia_usage()
    print(data)
    if not isinstance(data, list):
        data = []
    return data