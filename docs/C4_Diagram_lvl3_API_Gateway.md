flowchart TD
    subgraph API["API Gateway"]
        FastAPI["FastAPI App (main.py)<br/>Обрабатывает эндпоинты /generate, /test_*"]
        Router["Роутер (generate_code)<br/>Принимает Request, вызывает Оркестратор"]
        Storage["SessionStorage (history_db.py)<br/>CRUD операции с SQLite"]
        ResponseBuilder["Response Builder<br/>формирует JSON, добавляет код в ответ"]
    end

    Orch["Оркестратор"]
    SessionDB["Session Database (SQLite)"]

    FastAPI -- "маршрутизирует" --> Router
    Router -- "запускает оркестратор" --> Orch
    Router -- "сохраняет историю (промпт, ответ)" --> Storage
    Storage -- "читает/пишет (SQL)" --> SessionDB
    Router -- "упаковывает результат" --> ResponseBuilder
