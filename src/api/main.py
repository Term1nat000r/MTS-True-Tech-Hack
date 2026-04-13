from fastapi import FastAPI, HTTPException
from starlette import status

import uuid


# Импортируем ОРКЕСТРАТОР и реальные КЛАССЫ агентов
from src.agents.orchestrator import Orchestrator
from src.agents.generator import Generator
from src.agents.validator import Validator, Task, CodeResult
from src.agents.clarifier import Clarifier
from src.api.llm_client import LLMClient

from src.db.history_db import SessionStorage

# Контракты запросов
from src.agents.contracts.request_contract import Request

# Инициализируем клиент и реальных агентов
llm = LLMClient()
client = llm.get_instance()

history_storage = SessionStorage()

generator_agent = Generator(client=client)
validator_agent = Validator(client=client, history_storage=history_storage)
clarifier_agent = Clarifier(client=client, history_storage=history_storage)

current_session_id = None

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
    return generator_agent.generate("Напиши print('hello')")

@app.get("/test_val")
async def test_agent_validator():
    # Проверка работы критика
    task = Task(original_prompt="тест")
    code = CodeResult(code="lua{ print('hello') }lua", iteration=1)
    return validator_agent.validate(task, code)

@app.get("/test_cl")
async def test_agent_clarifier():
    # Проверка работы уточнения промпта
    return clarifier_agent.adapt("Сделай что-нибудь")

# Главный вход для жюри
@app.post("/generate")
async def generate_code(request: Request):
    # Запускаем "мозги" (оркестратор)
    result = await orchestrator.run(
        task=request.payload.raw_prompt,
        history=[],
        session_id=""
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

@app.post("/test_generate")
async def generate_code(req: Request):
    global current_session_id

    session_id = req.header.session_id or current_session_id or str(uuid.uuid4())

    if not current_session_id:
        current_session_id = session_id
        if not req.header.session_id:
            # Если не было текущей сессии и пользователь не выбрал сессию, то создать новую и добавить её в список сессий
            history_storage.append_sessions(session_id=session_id, chat_name=session_id)
    elif req.header.session_id:
        current_session_id = req.header.session_id


    task = req.payload.raw_prompt

    history = history_storage.get_session_history(session_id=session_id)

    # 2. Запускаем "мозги" (оркестратор)
    result = await orchestrator.run(
        task=task,
        history=history,
        session_id=session_id
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

    # Добавляем запрос пользователя в историю
    history_storage.append_history(session_id=session_id, role="user", content=task)

    # Вывод сообщения, если требуется уточнение
    if result.header.status == "clarification":
        # Добавляем ответ ассистента если нужно уточнение в историю
        history_storage.append_history(session_id=session_id, role="assistant", content=result.payload.display_text)
        response = {"session_id": session_id, "message": result.payload.display_text}
        if result.payload.content:
            response["code"] = result.payload.content
        return response

    # Добавляем ответ ассистента, если все гуд
    history_storage.append_history(session_id=session_id, role="assistant", content=result.payload.content)

    # 4. Возвращаем ответ в формате, который ждет жюри
    return {"code": result.payload.content}

# Возвращает историю определённой сессии
@app.get("/get_history/{session_id}")
async def get_history(session_id: str):
    history = history_storage.get_session_history(session_id=session_id)

    return {
        "session_id" : session_id,
        "history": [h.model_dump() for h in history]
    }

@app.get("/get_sessions")
async def get_sessions():
    sessions = history_storage.get_sessions()

    return {
        "sessions": sessions
    }

@app.get("/get_current_session")
async def get_current_session():
    return {"session_id": current_session_id}

@app.post("/change_session/{session_id}")
async def change_session(session_id: str):
    global current_session_id

    current_session_id = session_id

    return {"session_id": session_id}

@app.post("/create_session")
async def create_session():
    session_id = str(uuid.uuid4())
    history_storage.append_sessions(session_id=session_id, chat_name=session_id)

    return {"session_id": session_id, "chat_name": session_id}

@app.delete("/delete_session/{session_id}")
async def create_session(session_id: str):
    global current_session_id
    history_storage.delete_session(session_id=session_id)
    current_session_id = None

    return {"message": "Сессия успешно удалена"}

@app.get("/close_current_session")
async def close_current_session():
    global current_session_id
    current_session_id = None

    return {"message": "Сессия успешно покинута"}
