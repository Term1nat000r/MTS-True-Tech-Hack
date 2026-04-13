from fastapi import FastAPI
import uuid
from pydantic import BaseModel
# Импортируем ОРКЕСТРАТОР и реальные КЛАССЫ агентов
from src.agents.orchestrator import Orchestrator
from src.agents.generator import Generator
from src.agents.validator import Validator
from src.agents.clarifier import Clarifier

from src.api.llm_client import llm
from src.agents.contracts.request_contract import Request

client = llm.get_instance()
generator_agent = Generator(client=client)
validator_agent = Validator(client=client)
clarifier_agent = Clarifier(client=client)

orchestrator = Orchestrator(
    generator_agent=generator_agent,
    validator_agent=validator_agent,
    clarifier_agent=clarifier_agent
)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "MTS Lua Generator Active"}

@app.get("/test_gen")
async def test_agent_generator():
    return generator_agent.generate("Напиши print('hello')")

@app.get("/test_val")
async def test_agent_validator():
    from src.agents.validator import Task, CodeResult
    task = Task(original_prompt="тест")
    code = CodeResult(code="lua{ print('hello') }lua", iteration=1)
    return validator_agent.validate(task, code)

@app.get("/test_cl")
async def test_agent_clarifier():
    return clarifier_agent.adapt("Сделай что-нибудь")

@app.post("/generate")
async def generate_code(request: Request):
    result = await orchestrator.run(task=request.payload.raw_prompt)
    content = ""
    try:
        if hasattr(result, 'payload'):
            content = result.payload.content
        elif isinstance(result, dict):
            content = result.get("payload", {}).get("content", "")
    except Exception as e:
        print(f"Ошибка при разборе ответа: {e}")
        content = "Ошибка генерации кода"
    return {"code": content}

