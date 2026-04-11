# Главный файл сервера

from fastapi import FastAPI

from src.agents.orchestrator import Orchestrator
from src.agents.stubs import GeneratorAgent, ValidatorAgent, ClarifierAgent
from src.agents.contracts.base import StubAgentInput
from src.agents.contracts.request_contract import Request

generator_agent = GeneratorAgent()
validator_agent = ValidatorAgent()
clarifier_agent = ClarifierAgent()
orchestrator = Orchestrator(generator_agent=generator_agent, validator_agent=validator_agent, clarifier_agent=clarifier_agent)
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/test_gen")
async def test_agent_generator():
    result = await GeneratorAgent().run(StubAgentInput(data="Hello World"))
    return result

@app.get("/test_val")
async def test_agent_validator():
    result = await ValidatorAgent().run(StubAgentInput(data="Hello World"))
    return result

@app.get("/test_cl")
async def test_agent_clarifier():
    result = await ClarifierAgent().run(StubAgentInput(data="Hello World"))
    return result

@app.post("/generate")
async def generate_code(request: Request):
    result = await orchestrator.run(task=request.payload.raw_prompt, history=[h.model_dump() for h in request.payload.history])

    return result