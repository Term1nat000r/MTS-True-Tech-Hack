# Главный файл сервера

from fastapi import FastAPI

from src.agents.stubs import GeneratorAgent
from src.agents.contracts.base import StubAgentInput

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/test_gen")
async def test_agent_generator():
    result = await GeneratorAgent().run(StubAgentInput(data="Hello World"))
    return {"result": result}