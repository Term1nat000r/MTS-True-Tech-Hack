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

class Usage(BaseModel):
    total_tokens: int
    duration_ms: int

class Metadata(BaseModel):
    model: str
    usage: Usage

class ValidatorOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None

    @staticmethod
    def stub() -> "ValidatorOutput":
        header = Header(source_agent="generator", request_id="uuid", timestamp=0, status="success")
        payload = Payload(is_valid=True, recommendation="")

        usage = Usage(total_tokens=1, duration_ms=1)
        metadata = Metadata(model="qwen2.5:7b", usage=usage)

        return ValidatorOutput(header=header, payload=payload, metadata=metadata)