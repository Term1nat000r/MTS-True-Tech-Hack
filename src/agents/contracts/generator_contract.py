# Контракт вывода от агента-генератора

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str # "adapter" | "generator" | "validator"
    request_id: str
    timestamp: int
    status: str # "success" | "error" | "clarification"

class Payload(BaseModel):
    content: str
    explanation: str
    language: str

class Usage:
    total_tokens: int
    duration_ms: int

class Metadata:
    model: str
    usage: Usage

class GeneratorOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None