from fastapi import FastAPI, UploadFile, File, status, APIRouter, Depends
from fastapi.responses import StreamingResponse
import shutil
import os
import base64
from openai import OpenAI

from core.deps import get_model

router = APIRouter()

TEMP_DIR = "./tmp_images"
os.makedirs(TEMP_DIR, exist_ok=True)

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# --- Rota síncrona ---
@router.post("/ask_sync", description="Convert documents into clean Markdown files",status_code=status.HTTP_200_OK)
async def ask_sync(image: UploadFile = File(...),client: OpenAI = Depends(get_model)):

    temp_path = os.path.join(TEMP_DIR, image.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    data_url = f"data:image/jpeg;base64,{encode_image(temp_path)}"

    chat_response = client.chat.completions.create(
        model="numind/NuMarkdown-8B-Thinking",
        temperature=0.7,
        messages=[{
            "role": "user",
            "content": [{"type": "image_url", "image_url": {"url": data_url},
                         "min_pixels": 100*28*28, "max_pixels": 5000*28*28}]
        }],
    )

    result = chat_response.choices[0].message.content
    os.remove(temp_path)
    return {"response": result}

# --- Rota streaming ---
@router.post("/ask_stream", description="Convert documents into clean Markdown files", status_code=status.HTTP_200_OK)
async def ask_stream(image: UploadFile = File(...), client: OpenAI = Depends(get_model)):
    temp_path = os.path.join(TEMP_DIR, image.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(image.file, f)

    data_url = f"data:image/jpeg;base64,{encode_image(temp_path)}"

    def event_generator():
        stream = client.chat.completions.stream(
            model="numind/NuMarkdown-8B-Thinking",
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": [{"type": "image_url", "image_url": {"url": data_url},
                             "min_pixels": 100*28*28, "max_pixels": 5000*28*28}]
            }],
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
        os.remove(temp_path)

    return StreamingResponse(event_generator(), media_type="text/plain")
