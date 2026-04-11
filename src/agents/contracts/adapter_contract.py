# Контракт вывода от агента-адаптера

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str
    request_id: str
    timestamp: int
    status: str

class Payload(BaseModel):
    display_text: str
    refined_prompt: str
    is_ready: bool

class Usage:
    total_tokens: int
    duration_ms: int

class Metadata:
    model: str
    usage: Usage

class AdapterOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None