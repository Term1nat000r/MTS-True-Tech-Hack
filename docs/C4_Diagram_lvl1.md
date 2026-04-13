flowchart TD
    User["Разработчик / Жюри"]
    System["LocalScript\n(агентская система)"]
    Ollama["Ollama\n(локальная LLM)"]
    Docker["Docker\n(песочница)"]
    FS["Файловая система"]

    User -- "POST /generate (JSON)" --> System
    System -- "вызов LLM" --> Ollama
    System -- "запуск Lua кода" --> Docker
    System -- "чтение промптов, запись логов" --> FS
