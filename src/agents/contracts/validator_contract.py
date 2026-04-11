# Контракт вывода от агента-валидатора

from typing import List

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str
    request_id: str
    timestamp: int
    status: str

class Payload(BaseModel):
    is_valid: bool
    issues: List[str] | None = None
    recommendation: str

class Usage:
    total_tokens: int
    duration_ms: int

class Metadata:
    model: str
    usage: Usage

class ValidatorOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None