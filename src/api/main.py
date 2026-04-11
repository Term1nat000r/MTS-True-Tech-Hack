# Главный файл сервера

from fastapi import FastAPI

from src.agents.stubs import GeneratorAgent, ValidatorAgent, AdapterAgent
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

@app.get("/test_ad")
async def test_agent_adapter():
    result = await AdapterAgent().run(StubAgentInput(data="Hello World"))
    return result