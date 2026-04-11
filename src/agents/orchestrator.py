from src.agents.contracts.base import StubAgentInput, StubAgentOutput
from src.agents.contracts.orchestrator_contract import OrchestratorOutput
from src.agents.stubs import GeneratorAgent, ValidatorAgent, ClarifierAgent

class Orchestrator:
    async def run(self, inp: StubAgentInput) -> OrchestratorOutput:
        generator_result = await GeneratorAgent().run(StubAgentInput(data="Hello World"))
        if generator_result.header.status == "clarification":

            return OrchestratorOutput.stub(code="Clarification required")

        if generator_result.header.status == "error":
            return OrchestratorOutput.stub(code="error", error="An error occured")

        return OrchestratorOutput.stub(status="success" ,code="code")