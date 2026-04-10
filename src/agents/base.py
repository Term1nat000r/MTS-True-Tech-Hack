# Базовые классы агентов

from pydantic import BaseModel
from abc import ABC, abstractmethod

# Класс данных на ввод для агента
class AgentInput(BaseModel):
    query: str

# Класс данных вывода от агента
class AgentOutput(BaseModel):
    result: str

# Абстрактный базовый класс агента
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, input: AgentInput) -> AgentOutput:
        ...