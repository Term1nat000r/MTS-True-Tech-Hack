# Заглушки агентов

from agents.base import AgentInput, AgentOutput, BaseAgent

# Заглушка агента-генератора
class GeneratorAgent(BaseAgent):
    async def run(self, input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result=f"[ЗАГЛУШКА] Здесь будет сгенерированный агентом код"
        )

# Заглушка агента-валидатора кода
class ValidatorAgent(BaseAgent):
    async def run(self, input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result=f"[ЗАГЛУШКА] Здесь будет результат от агента-валидатора"
        )

# Заглушка агента-обработчика промптов
class ProcessorAgent(BaseAgent):
    async def run(self, input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result=f"[ЗАГЛУШКА] Здесь будет результат от агента-обработчика"
        )

class Orchestrator(BaseAgent):
    async def run(self, input: AgentInput) -> AgentOutput:
        return AgentOutput(
            result=f"[ЗАГЛУШКА] Здесь будет результат работы оркестратора"
        )