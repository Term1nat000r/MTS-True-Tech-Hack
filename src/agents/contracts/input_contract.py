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
    history: List[History] = []

# Класс данных на ввод для агента
class AgentInput(BaseModel):
    context: Context
    agent_config: AgentConfig
    data: Data

    @staticmethod
    def stub() -> "AgentInput":
        context = Context(session_id="uuid", request_id="uuid", timestamp=1)
        parameters = Parameters(temperature=1, stop_tokens=["\n"])
        agent_config = AgentConfig(target="", model="qwen2.5:7b", parameters=parameters)

        data = Data(input_text="Hello World")

        return AgentInput(context=context, agent_config=agent_config, data=data)