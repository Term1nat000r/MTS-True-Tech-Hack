C4Context
title Контекстная диаграмма — LocalScript: агентская система генерации Lua-кода

Person(developer, "Разработчик / Жюри", "Пользователь, отправляющий запросы на генерацию кода")
System(localScript, "LocalScript", "Агентская система для генерации и отладки Lua-кода (offline)")

System_Ext(ollama, "Ollama", "Локальный сервер LLM (DeepSeek-Coder, Llama 3, Qwen)")
System_Ext(docker, "Docker", "Изолированная песочница для запуска Lua-кода")
System_Ext(fs, "Файловая система", "Хранение промптов, логов, временных файлов")

Rel(developer, localScript, "Отправляет запрос через HTTP POST /generate", "JSON")
Rel(localScript, ollama, "Вызывает LLM для уточнения, генерации, валидации", "OpenAI API over HTTP")
Rel(localScript, docker, "Запускает Lua-код, ловит ошибки", "Docker API")
Rel(localScript, fs, "Читает промпты, пишет логи", "файловый ввод/вывод")

UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
