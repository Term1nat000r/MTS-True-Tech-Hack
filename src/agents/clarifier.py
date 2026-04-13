import json
import time
from openai import OpenAI
from src.api.config import Config


class Clarifier:
    def __init__(self, client: OpenAI, history_storage=None):
        self.client = client
        self.history_storage = history_storage
        with open(Config.PROMPTS_DIR / "clarifier.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

    def adapt(self, raw_input: str, history: list = None, session_id: str = "") -> dict:
        contract = {
            "header": {"source_agent": "adapter", "timestamp": int(time.time()), "status": "error"},
            "payload": {"display_text": "", "refined_prompt": None, "is_ready": False},
            "metadata": {"model": Config.MODEL_NAME, "usage": {"total_tokens": 0, "duration_ms": 0}},
            "error": None,
        }
        try:
            start = time.time()

            messages = [{"role": "system", "content": self.system_prompt}]
            for h in (history or []):
                role = h.role if h.role in ("user", "assistant") else "assistant"
                messages.append({"role": role, "content": h.content})
            messages.append({"role": "user", "content": raw_input})

            response = self.client.chat.completions.create(
                messages=messages,
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
            refined = llm_data.get("refined_prompt")
            is_ready = llm_data.get("is_ready", False)

            if is_ready and refined:
                contract["header"]["status"] = "success"
                contract["payload"]["refined_prompt"] = refined
                contract["payload"]["is_ready"] = True
            else:
                display = llm_data.get("display_text", "")
                contract["header"]["status"] = "clarification"
                contract["payload"]["display_text"] = display
                contract["payload"]["refined_prompt"] = refined
                contract["payload"]["is_ready"] = False

        except Exception as e:
            contract["error"] = {"message": str(e)}

        return contract
