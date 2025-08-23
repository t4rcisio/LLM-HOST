import datetime
import traceback

from fastapi import status
from fastapi import APIRouter
from fastapi import Depends
from fastapi.responses import JSONResponse

import ollama
from transformers import AutoTokenizer

from core.deps import start_ollama
from core import ECHO
import core.database as storage
from schema.chat_schema import ChatSchema
from fastapi.responses import StreamingResponse


router = APIRouter()


@router.get("/models", status_code=status.HTTP_200_OK, response_model=list)
async def get_models(_ = Depends(start_ollama)):
    try:
        modelos = ollama.list()
        return sorted([modelo['model'] for modelo in modelos['models']])
    except:
        return []


@router.post("/ask_sync", status_code=status.HTTP_200_OK, response_class=StreamingResponse)
async def ask_sync(message: ChatSchema, _ = Depends(start_ollama)):
    try:

        start = datetime.datetime.now()

        input_content = [{"role": "system", "content": message.template}, {"role": "user", "content": message.content}]

        response = ollama.chat(
            message.agent,
            input_content,
        )

        full_response = response['message']['content']

        # gravação de uso
        total_s = (datetime.datetime.now() - start).total_seconds() * 1_000_000_000
        output_tokens = count_tokens_qwen(full_response)
        input_tokens = count_tokens_qwen(str(input_content))

        total_tokens = input_tokens + output_tokens

        data = storage.ia_usage()
        if not isinstance(data, list):
            data = []

        data.append({
            "date": str(start),
            "total_seconds": total_s,
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "model_name": message.agent,
        })

        storage.ia_usage(data)

        return JSONResponse(content={"response": full_response})

    except:
        error = traceback.format_exc()
        return JSONResponse(status_code=500, content={"error": error})


@router.post("/ask_async", status_code=status.HTTP_200_OK, response_class=StreamingResponse)
async def ask_async(message: ChatSchema, _ = Depends(start_ollama)):
    async def stream_response():
        try:

            start = datetime.datetime.now()

            input_content = [{"role": "system", "content": message.template}, {"role": "user", "content": message.content}]

            response = ollama.chat(
                message.agent,
                input_content,
                stream=True
            )

            full_response = ""

            for chunk in response:
                content = chunk['message'].content
                full_response += content
                yield content

            # gravação de uso
            total_s = (datetime.datetime.now() - start).total_seconds() * 1_000_000_000
            output_tokens = count_tokens_qwen(full_response)
            input_tokens = count_tokens_qwen(str(input_content))

            total_tokens = input_tokens + output_tokens

            data = storage.ia_usage()
            if not isinstance(data, list):
                data = []

            data.append({
                "date": str(start),
                "total_seconds": total_s,
                "total_tokens": total_tokens,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model_name": message.agent,
            })

            storage.ia_usage(data)

        except Exception:
            error = traceback.format_exc()
            yield f"ERRO: {error}"

    return StreamingResponse(stream_response(), media_type="text/plain")



def count_tokens_qwen(text):
    try:
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen3-1.7B", trust_remote_code=True)
        return len(tokenizer.encode(text))
    except:
        return len(str(text).split(" "))
