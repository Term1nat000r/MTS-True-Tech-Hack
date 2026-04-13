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
        cl_res = self.clarifier.adapt(task, history=history, session_id=session_id)
        if cl_res["header"]["status"] == "clarification":
            # Вытаскиваем вопрос агента
            question = cl_res["payload"].get("display_text", "Мне нужно больше деталей для написания кода.")
            return OrchestratorOutput(
                header=cl_res["header"],
                payload=ClarificationPayload(
                    display_text=question,
                    refined_prompt=None,
                    # Заворачиваем вопрос в Lua-комментарий, чтобы фронт его показал!
                    content=f"jsonString lua{{\n-- [Уточняющий вопрос от AI]:\n-- {question}\n}}lua"
                ),
                metadata=cl_res["metadata"]
            )

        if cl_res["header"]["status"] == "error":
            return OrchestratorOutput(
                header=cl_res["header"],
                payload=ErrorPayload(display_text="Произошла ошибка в работе уточнителя", failed_agent="clarifier"),
                metadata=cl_res["metadata"],
                error=cl_res["error"]["message"]
            )

        refined_prompt = cl_res["payload"].get("refined_prompt") or task

        gen_res = self.generator.generate(refined_prompt, history=history)

        if gen_res["header"]["status"] == "error":
            error_msg = gen_res.get("error", {}).get("message", "Unknown logic error")
            return OrchestratorOutput(
                header={"source_agent": "orchestrator", "timestamp": gen_res["header"]["timestamp"], "status": "clarification"},
                payload=ClarificationPayload(
                    display_text=f"Я не могу сгенерировать код. Причина: {error_msg}",
                    refined_prompt=None,
                    content=f"jsonString lua{{ -- Ошибка генерации: {error_msg} }}lua"
                ),
                metadata=gen_res["metadata"]
            )

        code = gen_res["payload"]["content"]

        for i in range(1, 4):
            val_res = self.validator.validate(
                Task(original_prompt=refined_prompt, iteration=i),
                CodeResult(code=code, iteration=i),
                session_id=session_id
            )

            if val_res["header"]["status"] == "error":
                return OrchestratorOutput(
                    header=val_res["header"],
                    payload=ErrorPayload(display_text="Произошла ошибка в работе валидатора", failed_agent="validator"),
                    metadata=val_res["metadata"],
                    error = val_res["error"]["message"]
                )

            if val_res["payload"]["is_valid"]:
                break
            
            issues = val_res["payload"].get("issues", [])
            retry_prompt = f"Исправь ошибки в Lua коде: {issues}\nТЗ: {refined_prompt}\nТекущий код: {code}"

            gen_res = self.generator.generate(retry_prompt, history=history)
            if gen_res["header"]["status"] == "error":
                return OrchestratorOutput(
                    header=gen_res["header"],
                    payload=ErrorPayload(display_text="Произошла ошибка в работе генератора", failed_agent="generator"),
                    metadata=gen_res["metadata"],
                    error=gen_res["error"]["message"]
                )

            code = gen_res["payload"]["content"]

        if "payload" in gen_res:
            if "clarification_message" not in gen_res["payload"]:
                gen_res["payload"]["clarification_message"] = ""

        user_already_reviewed = any(h.role == "assistant" for h in history)

        if not user_already_reviewed:
            return OrchestratorOutput(
                header={"source_agent": "orchestrator", "timestamp": gen_res["header"]["timestamp"], "status": "clarification"},
                payload=ClarificationPayload(
                    display_text=f"Вот сгенерированный код:\n\n```lua\n{code}\n```\n\nПодтвердите или укажите, что изменить.",
                    refined_prompt=None,
                    content=code,
                ),
                metadata=gen_res["metadata"]
            )

        return OrchestratorOutput(**gen_res)
