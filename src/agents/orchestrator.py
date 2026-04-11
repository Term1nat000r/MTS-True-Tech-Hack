from typing import List

from src.agents.contracts.base import StubAgentInput, StubAgentOutput
from src.agents.stubs import GeneratorAgent, ValidatorAgent, ClarifierAgent
from src.agents.contracts.input_contract import AgentInput, History
from src.agents.contracts.orchestrator_contract import OrchestratorOutput

class Orchestrator:
    def __init__(self, generator_agent: GeneratorAgent, validator_agent: ValidatorAgent, clarifier_agent: ClarifierAgent):
        self.generator = generator_agent
        self.validator = validator_agent
        self.clarifier = clarifier_agent

    async def run(self, task: str, history: list) -> OrchestratorOutput:
        messages = history + [History(role="user", content = task)]

        generator_result = await self.generator.run(StubAgentInput(data="Hello World"))

        if generator_result.header.status == "error":

            # Вернуть ошибку
            return OrchestratorOutput.stub()

        if generator_result.header.status == "clarification":
            clarifier_result = await self.clarifier.run()

            if clarifier_result.header.status == "error":

                # Вернуть ошибку
                return OrchestratorOutput.stub()

            updated_history = messages + [History(role="assistant", content=clarifier_result.payload.refined_prompt)]

            # Сделать тип для вывода
            return OrchestratorOutput.stub()

        max_retries = 3
        code = generator_result.payload.content
        for i in range(max_retries):
            validator_result =  await self.validator.run()

            if validator_result.header.status == "success":

                # Сделать вывод
                return OrchestratorOutput.stub()

            messages = messages + [History(role="assistant", content= code),
                                   History(role="user", content=f"Код содержит ошибки: {validator_result.payload.issues}. Исправь.")]

            generator_result = await self.generator.run()
            code = generator_result.payload.content


        # Вернуть ошибку
        return OrchestratorOutput.stub()