# Контракт вывода от оркестратора

from typing import List, Union

from pydantic import BaseModel

class Header(BaseModel):
    source_agent: str = "orchestrator"
    request_id: str
    timestamp: int
    status: str

class History(BaseModel):
    role: str
    content: str

class Usage(BaseModel):
    total_tokens: int
    duration_ms: int

class Metadata(BaseModel):
    usage: Usage

class ClarificationPayload(BaseModel):
    display_text: str
    refined_prompt: str | None = None
    is_ready: bool

class ErrorPayload(BaseModel):
    display_text: str
    failed_agent: str

class ResultPayload(BaseModel):
    content: str
    language: str = "lua"
    explanation: str
    clarification_message: str
    history: List[History] = []

class OrchestratorOutput(BaseModel):
    header: Header
    payload: Union[ResultPayload, ClarificationPayload, ErrorPayload]
    metadata: Metadata
    error: str | None = None

    @staticmethod
    def stub() -> "OrchestratorOutput":
        header = Header(request_id="uuid", timestamp=0, status="success")
        payload = ResultPayload(content="Hello World", explanation="explanation", clarification_message="clarification message")
        usage = Usage(total_tokens=1, duration_ms=1)
        metadata = Metadata(usage=usage)

        return OrchestratorOutput(header=header, payload=payload, metadata=metadata)