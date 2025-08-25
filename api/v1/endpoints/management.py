import asyncio

from fastapi import APIRouter
import core.database as storage
from schema.log_schema import LogEntry

router = APIRouter()


from typing import List

@router.get("/dashboard", response_model=List[LogEntry])
async def get_logs():

    loop = asyncio.get_event_loop()

    data = await loop.run_in_executor(
        None,  # usa ThreadPoolExecutor padrão
        lambda: storage.ia_usage()
    )
    if not isinstance(data, list):
        data = []
    return data