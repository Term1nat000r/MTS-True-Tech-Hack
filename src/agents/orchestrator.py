from agents.contracts.base import StubAgentInput, StubAgentOutput
from agents.contracts.base import BaseAgent
from agents.stubs import GeneratorAgent, ValidatorAgent, ClarifierAgent

class Orchestrator(BaseAgent):
    async def run(self, inp: StubAgentInput) -> StubAgentOutput:
        generator_result = await GeneratorAgent().run(StubAgentInput(data="Hello World"))
        if generator_result.header.status == "clarification":
            return StubAgentOutput(result="Awaiting clarification")


        return StubAgentOutput(result="Code generated successfully")