# Контракт вывода от агента-генератора

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str # "adapter" | "generator" | "validator"

    timestamp: int
    status: str # "success" | "error" | "clarification"

class Payload(BaseModel):
    content: str
    explanation: str
    language: str = "lua"

class Usage(BaseModel):
    total_tokens: int
    duration_ms: int

class Metadata(BaseModel):
    model: str
    usage: Usage

class GeneratorOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None

    @staticmethod
    def stub() -> "GeneratorOutput":
        header = Header(source_agent="generator", request_id="uuid", timestamp=0, status="success")
        payload = Payload(content="Hello World", explanation="explanation", language="lua")

        usage = Usage(total_tokens=1, duration_ms=1)
        metadata = Metadata(model="qwen2.5:7b", usage=usage)

        return GeneratorOutput(header=header, payload=payload, metadata=metadata)