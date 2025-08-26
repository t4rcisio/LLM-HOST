import asyncio

from fastapi import APIRouter
import core.database as storage
from core.logs import LogManager
from schema.log_schema import LogEntry, SysLogEntry

router = APIRouter()


from typing import List

@router.get("/ia", response_model=List[LogEntry])
async def get_ai_logs():

    loop = asyncio.get_event_loop()

    data = await loop.run_in_executor(
        None,  # usa ThreadPoolExecutor padrão
        lambda: storage.ia_usage()
    )
    if not isinstance(data, list):
        data = []
    return data


@router.get("/logs", response_model=List[SysLogEntry])
async def get_sys_logs():
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None,
        lambda: LogManager.read_logs()
    )
    return data  # retorna direto a lista