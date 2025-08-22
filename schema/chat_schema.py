from pydantic import BaseModel
from typing import Optional


class ChatSchema(BaseModel):
    agent: str
    content: str
    template: str


    user_key: Optional[str] = None
    project: Optional[str] = None
    process_id: Optional[str] = None
    subprocess_id: Optional[str] = None

    class Config:
        orm_mode = True


