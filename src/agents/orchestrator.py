import time
from src.agents.contracts.orchestrator_contract import OrchestratorOutput
from src.agents.validator import Task, CodeResult


class Orchestrator:
    def __init__(self, generator_agent, validator_agent, clarifier_agent):
        self.generator = generator_agent
        self.validator = validator_agent
        self.clarifier = clarifier_agent

    async def run(self, task: str) -> OrchestratorOutput:
        cl_res = self.clarifier.adapt(task)
        clarification_msg = cl_res["payload"].get("display_text", "")
        refined_prompt = cl_res["payload"].get("refined_prompt")

        # If clarifier couldn't form a refined prompt, return clarification only
        if not refined_prompt:
            return OrchestratorOutput(
                header={"source_agent": "orchestrator", "timestamp": int(time.time()), "status": "clarification"},
                payload={"content": "", "language": "lua", "explanation": "", "clarification_message": clarification_msg},
                metadata={"usage": {"total_tokens": 0, "duration_ms": 0}},
            )

        gen_res = self.generator.generate(refined_prompt)
        gen_res["payload"]["clarification_message"] = clarification_msg
        code = gen_res["payload"]["content"]

        for i in range(1, 4):
            val_res = self.validator.validate(
                Task(original_prompt=refined_prompt, iteration=i),
                CodeResult(code=code, iteration=i),
            )
            if val_res["payload"]["is_valid"]:
                return OrchestratorOutput(**gen_res)
            issues = val_res["payload"].get("issues", [])
            gen_res = self.generator.generate(
                f"Исправь ошибки в Lua коде: {issues}\nТЗ: {refined_prompt}\nТекущий код: {code}"
            )
            gen_res["payload"]["clarification_message"] = clarification_msg
            code = gen_res["payload"]["content"]

        return OrchestratorOutput(**gen_res)
