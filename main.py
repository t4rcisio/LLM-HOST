from fastapi import FastAPI
from core.configs import settings

from api.v1 import api

import os
import platform
system = platform.system()

if system in ["Windows", "Linux"]:
    os.environ["OLLAMA_NUM_PARALLEL"] = "4"
    print(f"Variável OLLAMA_NUM_PARALLEL=4 criada no {system}")




app = FastAPI(title="AI HOST", version="0.0.1", description="AI OLLAMA HOST")
app.include_router(api.api_router, prefix=settings.API_V1_STR)

host_ = settings.URL.split("//")[-1]

@app.get("/")
async def main():
    return {"server": "AI HOST is running"}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=host_, port=int(settings.PORT), log_level="info", workers=5)