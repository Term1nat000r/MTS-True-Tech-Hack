# Контракт вывода от агента-уточнителя
from typing import List

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str = "user"
    session_id: str = ""
    status: str = "new"

class Settings(BaseModel):
    target_language: str = "ru"
    mode: str = "code_generation"
    stream: bool = False

class History(BaseModel):
    role: str
    content: str

class Payload(BaseModel):
    raw_prompt: str
    settings: Settings
    history: List[History] = []

class Metadata(BaseModel):
    timestamp: int

class Request(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata

    @staticmethod
    def stub() -> "Request":
        header = Header(request_id="uuid")
        settings = Settings()
        payload = Payload(raw_prompt="Hello World", settings=settings)
        metadata = Metadata(timestamp=1)

        return Request(header=header, payload=payload, metadata=metadata)