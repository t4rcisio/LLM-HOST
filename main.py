from fastapi import FastAPI
from core.configs import settings

from api.v1 import api

app = FastAPI(title="AI HOST", version="0.0.1", description="AI OLLAMA HOST")
app.include_router(api.api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def main():
    return {"server": "AI HOST is running"}



if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info", reload=True)