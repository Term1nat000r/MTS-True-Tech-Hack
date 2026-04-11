# Заглушки агентов

from agents.contracts.generator_contract import GeneratorOutput, Header, Payload, Metadata
from src.agents.contracts.base import BaseAgent, StubAgentOutput, StubAgentInput
# from agents.contracts.validator_contract import ValidatorOutput
# from agents.contracts.adapter_contract import AdapterOutput

# Заглушка агента-генератора
class GeneratorAgent(BaseAgent):
    async def run(self, inp: StubAgentInput) -> GeneratorOutput:
        return GeneratorOutput(
            header=Header(source_agent=""),
            payload= Payload(),
            metadata= Metadata(),
            error= None
        )

# Заглушка агента-валидатора кода
class ValidatorAgent(BaseAgent):
    async def run(self, inp: StubAgentInput) -> StubAgentOutput:
        return StubAgentOutput(
            result=f"[ЗАГЛУШКА] Здесь будет результат агента-валидатора"
        )

# Заглушка агента-обработчика промптов
class ClarifierAgent(BaseAgent):
    async def run(self, inp: StubAgentInput) -> StubAgentOutput:
        return StubAgentOutput(
            result=f"[ЗАГЛУШКА] Здесь будет результат агента-уточнителя"
        )