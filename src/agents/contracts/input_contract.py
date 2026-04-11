from typing import List
from pydantic import BaseModel

class Context(BaseModel):
    session_id: str
    request_id: str
    timestamp: int

class Parameters(BaseModel):
    temperature: float

    # МОЖЕТ ЛИ БЫТЬ ПУСТЫМ?
    stop_tokens: List[str]

class AgentConfig(BaseModel):
    target: str
    model: str
    parameters: Parameters

class History(BaseModel):
    role: str
    content: str

class Data(BaseModel):
    input_text: str

    # МОЖЕТ ЛИ БЫТЬ ПУСТЫМ?
    history: List[History]

# Класс данных на ввод для агента
class AgentInput(BaseModel):
    context: Context
    agent_config: AgentConfig
    data: Data