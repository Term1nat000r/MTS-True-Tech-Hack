# Контракт вывода от оркестратора

from typing import List

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str = "orchestrator"

    timestamp: int
    status: str

class History(BaseModel):
    role: str
    content: str

class Payload(BaseModel):
    content: str
    language: str = "lua"
    explanation: str
    clarification_message: str
    history: List[History] = []

class Usage(BaseModel):
    total_tokens: int
    duration_ms: int

class Metadata(BaseModel):
    usage: Usage

class OrchestratorOutput(BaseModel):
    header: Header
    payload: Payload
    metadata: Metadata
    error: str | None = None

    @staticmethod
    def stub() -> "OrchestratorOutput":
        header = Header(request_id="uuid", timestamp=0, status="success")
        payload = Payload(content="Hello World", explanation="explanation", clarification_message="clarification message")
        usage = Usage(total_tokens=1, duration_ms=1)
        metadata = Metadata(usage=usage)

        return OrchestratorOutput(header=header, payload=payload, metadata=metadata)