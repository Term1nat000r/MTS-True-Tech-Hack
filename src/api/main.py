from fastapi import FastAPI, HTTPException
from starlette import status

import uuid
from pydantic import BaseModel
# Импортируем ОРКЕСТРАТОР и реальные КЛАССЫ агентов
from src.agents.orchestrator import Orchestrator
from src.agents.generator import Generator
from src.agents.validator import Validator, Task, CodeResult
from src.agents.clarifier import Clarifier
from src.api.llm_client import LLMClient

from src.agents.contracts.request_contract import Request

# Инициализируем клиент и реальных агентов
llm = LLMClient()
client = llm.get_instance()

generator_agent = Generator(client=client)
validator_agent = Validator(client=client)
clarifier_agent = Clarifier(client=client)

# Создаем оркестратор с реальными агентами
orchestrator = Orchestrator(
    generator_agent=generator_agent,
    validator_agent=validator_agent,
    clarifier_agent=clarifier_agent
)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "MTS Lua Generator Active"}

# Твои тестовые эндпоинты (теперь работают с реальным AI)
@app.get("/test_gen")
async def test_agent_generator():
    return generator_agent.generate("Напиши print('hello')", str(uuid.uuid4()))

@app.get("/test_val")
async def test_agent_validator():
    # Проверка работы критика
    task = Task(original_prompt="тест", request_id=str(uuid.uuid4()))
    code = CodeResult(code="lua{ print('hello') }lua", iteration=1)
    return validator_agent.validate(task, code)

@app.get("/test_cl")
async def test_agent_clarifier():
    # Проверка работы уточнения промпта
    return clarifier_agent.adapt("Сделай что-нибудь", str(uuid.uuid4()))

# Главный вход для жюри
@app.post("/generate")
async def generate_code(request: Request):
    # 1. Генерируем ID запроса, если его нет
    req_id = request.header.request_id or str(uuid.uuid4())

    # 2. Запускаем "мозги" (оркестратор)
    result = await orchestrator.run(
        task=request.payload.raw_prompt,
        request_id=req_id
    )

    # 3. Безопасно достаем код (проверяем, объект это или словарь)
    content = ""
    try:
        # Если оркестратор вернул объект OrchestratorOutput
        if hasattr(result, 'payload'):
            content = result.payload.content
        # Если оркестратор вернул обычный словарь
        elif isinstance(result, dict):
            content = result.get("payload", {}).get("content", "")
    except Exception as e:
        print(f"Ошибка при разборе ответа: {e}")
        content = "Ошибка генерации кода"

    # 4. Возвращаем ответ в формате, который ждет жюри
    return {"code": content}

@app.get("/test_generate")
async def generate_code():
    # 1. Генерируем ID запроса, если его нет
    req_id = str(uuid.uuid4())

    # 2. Запускаем "мозги" (оркестратор)
    result = await orchestrator.run(
        task="Помоги мне",
        request_id=req_id
    )

    # Если при работе оркестратора произошла ошибка
    if result.header.status == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": result.payload.display_text,
                "error": result.error,
                "failed_agent": result.payload.failed_agent
            }
        )

    # Вывод сообщения, если требуется уточнение
    if result.header.status == "clarification":
        return {"message": result.payload.display_text}

    # 4. Возвращаем ответ в формате, который ждет жюри
    return {"code": result.payload.content}
