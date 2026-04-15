# Контракт вывода от агента-уточнителя

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str

    timestamp: int
    status: str

class Payload(BaseModel):
    display_text: str
    refined_prompt: str
    is_ready: bool

class Usage(BaseModel):
    total_tokens: int
    duration_ms: int

class Metadata(BaseModel):
    model: str
    usage: Usage

class ClarifierOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None

    @staticmethod
    def stub() -> "ClarifierOutput":
        header = Header(source_agent="generator", request_id="uuid", timestamp=0, status="success")
        payload = Payload(display_text="Hello World", refined_prompt="refined prompt", is_ready=True)

        usage = Usage(total_tokens=1, duration_ms=1)
        metadata = Metadata(model="qwen2.5:7b", usage=usage)

        return ClarifierOutput(header=header, payload=payload, metadata=metadata)