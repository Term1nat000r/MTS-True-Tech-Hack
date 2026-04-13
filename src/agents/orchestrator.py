from src.agents.contracts.input_contract import History
from src.agents.contracts.orchestrator_contract import ErrorPayload
from src.agents.contracts.orchestrator_contract import ClarificationPayload
from src.agents.contracts.orchestrator_contract import OrchestratorOutput
from src.agents.validator import Task, CodeResult

class Orchestrator:
    def __init__(self, generator_agent, validator_agent, clarifier_agent):
        self.generator = generator_agent
        self.validator = validator_agent
        self.clarifier = clarifier_agent

    async def run(self, task: str, history: list[History], session_id: str = "") -> OrchestratorOutput:

        # 1. Уточнение задачи
        cl_res = self.clarifier.adapt(task, session_id=session_id)
        if cl_res["header"]["status"] == "clarification":
            return OrchestratorOutput(
                header=cl_res["header"],
                payload=ClarificationPayload(**cl_res["payload"]),
                metadata=cl_res["metadata"]
            )

        # Если уточнитель выдал ошибку
        if cl_res["header"]["status"] == "error":
            return OrchestratorOutput(
                header=cl_res["header"],
                payload=ErrorPayload(display_text="Произошла ошибка в работе уточнителя", failed_agent="clarifier"),
                metadata=cl_res["metadata"],
                error=cl_res["error"]["message"]
            )

        refined_prompt = cl_res["payload"].get("refined_prompt") or task

        # Достаём предыдущий код из истории (если это второй круг)
        previous_code = None
        for h in reversed(history):
            if h.role == "validator":
                previous_code = h.content
                break

        # 2. Первая попытка генерации кода
        if previous_code:
            gen_prompt = f"Предыдущий код:\n{previous_code}\n\nПравки пользователя: {refined_prompt}\n\nИсправь код согласно правкам."
        else:
            gen_prompt = refined_prompt

        gen_res = self.generator.generate(gen_prompt)

        # Если генератор выдал ошибку
        if gen_res["header"]["status"] == "error":
            return OrchestratorOutput(
                header=gen_res["header"],
                payload=ErrorPayload(display_text="Произошла ошибка в работе генератора", failed_agent="generator"),
                metadata=gen_res["metadata"],
                error=gen_res["error"]["message"]
            )

        code = gen_res["payload"]["content"]

        # 3. Цикл самоисправления (до 3-х попыток)
        for i in range(1, 4):
            val_res = self.validator.validate(
                Task(original_prompt=refined_prompt, iteration=i),
                CodeResult(code=code, iteration=i),
                session_id=session_id
            )

            # Если валидатор выдал ошибку
            if val_res["header"]["status"] == "error":
                return OrchestratorOutput(
                    header=val_res["header"],
                    payload=ErrorPayload(display_text="Произошла ошибка в работе валидатора", failed_agent="validator"),
                    metadata=val_res["metadata"],
                    error = val_res["error"]["message"]
                )

            # Если валидатор подтвердил код — выходим
            if val_res["payload"]["is_valid"]:
                break
            
            # Если есть ошибки — просим генератор исправить их
            issues = val_res["payload"].get("issues", [])
            retry_prompt = f"Исправь ошибки в Lua коде: {issues}\nТЗ: {refined_prompt}\nТекущий код: {code}"

            gen_res = self.generator.generate(retry_prompt)
            # Если генератор выдал ошибку
            if gen_res["header"]["status"] == "error":
                return OrchestratorOutput(
                    header=gen_res["header"],
                    payload=ErrorPayload(display_text="Произошла ошибка в работе генератора", failed_agent="generator"),
                    metadata=gen_res["metadata"],
                    error=gen_res["error"]["message"]
                )

            code = gen_res["payload"]["content"]

        # Перед тем как отдавать результат, добавим пустое поле, которое требует контракт
        if "payload" in gen_res:
            if "clarification_message" not in gen_res["payload"]:
                gen_res["payload"]["clarification_message"] = ""

        # 4. Проверяем, видел ли пользователь код ранее (есть ли запись validator в истории)
        user_already_reviewed = any(h.role == "validator" for h in history)

        if not user_already_reviewed:
            # Первый прогон — отправляем код пользователю на просмотр
            return OrchestratorOutput(
                header={"source_agent": "orchestrator", "timestamp": gen_res["header"]["timestamp"], "status": "clarification"},
                payload=ClarificationPayload(
                    display_text=f"Вот сгенерированный код:\n\n```lua\n{code}\n```\n\nПодтвердите или укажите, что изменить.",
                    refined_prompt=None,
                    content=code,
                ),
                metadata=gen_res["metadata"]
            )

        # Второй прогон — отдаём финальный результат
        return OrchestratorOutput(**gen_res)
