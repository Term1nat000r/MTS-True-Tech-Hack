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

    async def run(self, task: str, request_id: str, history: list[History]) -> OrchestratorOutput:

        # 1. Уточнение задачи
        cl_res = self.clarifier.adapt(task, request_id)
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
        
        # 2. Первая попытка генерации кода
        gen_res = self.generator.generate(refined_prompt, request_id)
        code = gen_res["payload"]["content"]

        # Если генератор выдал ошибку
        if gen_res["header"]["status"] == "error":
            return OrchestratorOutput(
                header=gen_res["header"],
                payload=ErrorPayload(display_text="Произошла ошибка в работе генератора", failed_agent="generator"),
                metadata=gen_res["metadata"],
                error=gen_res["error"]["message"]
            )

        # 3. Цикл самоисправления (до 3-х попыток)
        for i in range(1, 4):
            val_res = self.validator.validate(
                Task(original_prompt=refined_prompt, request_id=request_id, iteration=i),
                CodeResult(code=code, iteration=i)
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
                return OrchestratorOutput(**gen_res)
            
            # Если есть ошибки — просим генератор исправить их
            issues = val_res["payload"].get("issues", [])
            retry_prompt = f"Исправь ошибки в Lua коде: {issues}\nТЗ: {refined_prompt}\nТекущий код: {code}"

            gen_res = self.generator.generate(retry_prompt, request_id)
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

        return OrchestratorOutput(**gen_res)
