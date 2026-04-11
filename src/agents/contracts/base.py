# Базовые классы агентов
from typing import List

from pydantic import BaseModel
from abc import ABC, abstractmethod

class StubAgentInput(BaseModel):
    data: str

# Класс данных вывода от агента
class StubAgentOutput(BaseModel):
    result: str

# Абстрактный базовый класс агента
class BaseAgent(ABC):
    @abstractmethod
    async def run(self, inp: StubAgentInput) -> StubAgentOutput:
        ...