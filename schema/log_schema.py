


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



class SysLogEntry(BaseModel):
    date: datetime
    level: str
    message: str
    source: Optional[str] = None
    user_id: Optional[str] = None
    ip: Optional[str] = None

    class Config:
        orm_mode = True