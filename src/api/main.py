# Главный файл сервера

from fastapi import FastAPI

from src.agents.orchestrator import Orchestrator
from src.agents.stubs import GeneratorAgent, ValidatorAgent, ClarifierAgent
from src.agents.contracts.base import StubAgentInput

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

@app.get("/test_orc")
async def test_orchestrator():
    result = await Orchestrator().run(StubAgentInput(data="Hello World"))
    return result