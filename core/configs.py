
from pydantic_settings import BaseSettings


class Settings:

    URL: str =  "http://0.0.0.0"
    PORT: str = "5000"
    API_V1_STR: str = "/api/v1"
    VLLM_API_KEY = "EMPTY"
    VLLM_API_BASE = "http://localhost:8000/v1"

    WORKERS: int = 3
    OLLAMA_NUM_PARALLEL: int = 2



    class Config:
        case_sensitive = True


settings: Settings = Settings()

