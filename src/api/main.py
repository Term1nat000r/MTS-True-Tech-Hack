# Главный файл сервера

from fastapi import FastAPI

from src.agents.stubs import GeneratorAgent
from src.agents.contracts.base import StubAgentInput

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}
