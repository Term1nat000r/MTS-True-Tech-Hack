import json
import time
from openai import OpenAI
from src.api.config import Config

FIXED_QUESTION = "Укажите, пожалуйста, какие переменные (wf.vars) используются в вашем бизнес-процессе и какие данные они содержат?"


class Clarifier:
    def __init__(self, client: OpenAI):
        self.client = client
        with open(Config.PROMPTS_DIR / "clarifier.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

    def adapt(self, raw_input: str) -> dict:
        contract = {
            "header": {"source_agent": "adapter", "timestamp": int(time.time()), "status": "error"},
            "payload": {"display_text": "", "refined_prompt": None, "is_ready": False},
            "metadata": {"model": Config.MODEL_NAME, "usage": {"total_tokens": 0, "duration_ms": 0}},
            "error": None,
        }
        try:
            start = time.time()
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": raw_input},
                ],
                **Config.get_llm_params(),
            )
            contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start) * 1000)
            if hasattr(response, "usage") and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = getattr(response.usage, "total_tokens", 0)

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.strip("`").strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            llm_data = json.loads(raw)

            # Always include at least one fixed clarifying question
            display = llm_data.get("display_text", "")
            if FIXED_QUESTION not in display:
                display = f"{display}\n\n{FIXED_QUESTION}".strip()

            contract["header"]["status"] = "clarification"
            contract["payload"]["display_text"] = display
            contract["payload"]["refined_prompt"] = llm_data.get("refined_prompt")
            contract["payload"]["is_ready"] = False

        except Exception as e:
            contract["error"] = {"message": str(e)}

        return contract
