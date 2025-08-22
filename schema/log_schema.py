


from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LogEntry(BaseModel):

    date: datetime
    total_seconds: float
    total_tokens: int
    input_tokens: int
    output_tokens: int
    model_name: str



    class Config:
        orm_mode = True