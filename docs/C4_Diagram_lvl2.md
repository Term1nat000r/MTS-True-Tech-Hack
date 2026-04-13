flowchart TD
    Developer["Разработчик / Жюри"]

    subgraph LocalScript["LocalScript"]
        API["API Gateway (FastAPI)<br/>Принимает запросы, возвращает код, сохраняет историю"]
        Orch["Оркестратор (Python + LangGraph)<br/>Управляет циклом Clarifier → Generator → Validator"]
        Clarifier["Clarifier Agent (Python)<br/>Уточняет промпт"]
        Generator["Generator Agent (Python)<br/>Генерирует Lua-код"]
        Validator["Validator Agent (Python)<br/>Проверяет код (luac + LLM)"]
        KB["База знаний (файлы + ChromaDB)<br/>Правила платформы и примеры"]
        LLMClient["LLM Client (OpenAI SDK)<br/>Абстракция над Ollama"]
        SessionDB["Session Database (SQLite)<br/>Хранит историю сессий и список чатов"]
    end

    Ollama["Ollama (локальная LLM)"]
    Docker["Docker (песочница)"]
    FS["Файловая система (промпты, логи)"]

    Developer -- "POST /generate (JSON)" --> API
    API -- "вызывает run()" --> Orch
    API -- "сохраняет историю (SQLite)" --> SessionDB

    Orch -- "adapt()" --> Clarifier
    Orch -- "generate()" --> Generator
    Orch -- "validate()" --> Validator

    Clarifier -- "использует" --> LLMClient
    Generator -- "использует" --> LLMClient
    Validator -- "использует" --> LLMClient

    Generator -- "читает правила" --> KB
    Validator -- "читает правила" --> KB

    LLMClient -- "HTTP" --> Ollama
    Validator -- "запускает код (планируется)" --> Docker
    SessionDB -- "хранит .db файл" --> FS
