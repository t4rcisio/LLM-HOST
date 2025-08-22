
from pydantic_settings import BaseSettings


class Settings:


    API_V1_STR: str = "/api/v1"
    VLLM_API_KEY = "EMPTY"
    VLLM_API_BASE = "http://localhost:8000/v1"



    class Config:
        case_sensitive = True


settings: Settings = Settings()

