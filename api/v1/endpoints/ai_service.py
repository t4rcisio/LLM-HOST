
import datetime
import traceback
import uuid

from fastapi import status
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse

import ollama
from transformers import AutoTokenizer

from core.deps import start_ollama
import core.database as storage
from core.logs import LogManager
from schema.chat_schema import ChatSchema, agentSchema
from fastapi.responses import StreamingResponse

from schema.log_schema import SysLogEntry

router = APIRouter()

from concurrent.futures import ThreadPoolExecutor
import os

executor = ThreadPoolExecutor(max_workers=os.cpu_count())

from core import ollama_server
olla_queue = ollama_server.OllamaQueue()

import asyncio



@router.get("/models", status_code=status.HTTP_200_OK, response_model=list)
async def get_models(_ = Depends(start_ollama)):
    try:

        loop = asyncio.get_event_loop()

        modelos = await loop.run_in_executor(
            executor,
            lambda:ollama.list()
        )
        return sorted([modelo['model'] for modelo in modelos['models']])
    except:

        dataLogs = LogManager()
        log = SysLogEntry(date=datetime.datetime.now(), level="ERRO", message=traceback.format_exc(), source="/models")
        dataLogs.write_log(log)
        return []


@router.post("/download", status_code=status.HTTP_200_OK)
async def download(message: agentSchema, server = Depends(olla_queue.start)):
    try:
        response = server['CLIENT'].pull(message.agent,insecure=True)
        resp = await  get_models()

        if message.agent in resp:
            return JSONResponse(content={"response": f"Success to download {message.agent} model"})
        else:
            return JSONResponse(status_code=500, content={"error": f"Failed to download {message.agent} model\t" + str(response)})
    except:
        dataLogs = LogManager()
        log = SysLogEntry(date=datetime.datetime.now(), level="ERRO", message=traceback.format_exc(), source="/download")
        dataLogs.write_log(log)
        return JSONResponse(status_code=500, content={"error": "Ocorreu um erro ao processar a solicitação"})



@router.get("/job/{job_id}", status_code=status.HTTP_200_OK)
async def jobs_(job_id: str):

    data = storage.queue()
    if not isinstance(data, dict):
        data = {}

    if job_id not in data:
        return {"error": "job não encontrado"}

    return data[job_id]


@router.post("/new/job", status_code=status.HTTP_200_OK)
async def ask_sync(message: ChatSchema):
    data = storage.queue()

    if not isinstance(data, dict):
        data = {}

    job_id = str(uuid.uuid4())

    data[job_id] = {"ID": job_id,
                    "QUEUED": str(datetime.datetime.now()),
                    "PARAMS": {"agent": message.agent,
                               "template": message.template,
                               "content": message.content,
                               },
                    "RESULT":"",
                    "STATE": "ON QUEUE"}

    storage.queue(data)
    return {"ID": job_id, 'STATUS': "ON QUEUE"}

