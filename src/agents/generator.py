import json
import re
import time
from openai import OpenAI
from src.api.knowledge import get_generator_system_prompt
from src.api.config import Config


class Generator:
    _RE_LUA_BLOCK = re.compile(r"```lua\s*(.*?)```", re.DOTALL | re.IGNORECASE)
    _RE_ANY_BLOCK = re.compile(r"```[a-zA-Z0-9_+-]*\s*(.*?)```", re.DOTALL)
    _RE_LOWCODE_WRAP = re.compile(r"jsonString\s+lua\s*\{(.*)\}\s*lua\s*$", re.DOTALL | re.IGNORECASE)

    def __init__(self, client: OpenAI):
        self.client = client
        with open(Config.PROMPTS_DIR / "generator.txt", "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
        self.system_prompt = get_generator_system_prompt(base_prompt)

    def generate(self, refined_prompt: str) -> dict:
        start = time.time()
        contract = {
            "header": {"source_agent": "generator", "timestamp": int(start), "status": "error"},
            "payload": {"content": "", "lua_code": "", "explanation": "", "language": "lua", "clarification_message": ""},
            "metadata": {"model": Config.MODEL_NAME, "usage": {"total_tokens": 0, "duration_ms": 0}},
            "error": None,
        }
        raw_result = ""
        try:
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": refined_prompt},
                ],
                **Config.get_llm_params(),
            )
            contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start) * 1000)
            if hasattr(response, "usage") and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = getattr(response.usage, "total_tokens", 0)

            if not response.choices or not response.choices[0].message.content:
                contract["error"] = {"message": "Empty response from model"}
                return contract

            raw_result = response.choices[0].message.content.strip()
            parsed = self._parse_model_output(raw_result)

            contract["header"]["status"] = "success"
            contract["payload"]["content"] = parsed["content"]
            contract["payload"]["lua_code"] = self._strip_lowcode_wrap(parsed["content"])
            contract["payload"]["explanation"] = parsed["explanation"]
            contract["payload"]["language"] = parsed["language"]

            if not parsed["content"].strip():
                contract["header"]["status"] = "error"
                contract["error"] = {"message": "Could not extract Lua code", "raw_response": raw_result}

        except json.JSONDecodeError:
            contract["error"] = {"message": "Invalid output format", "raw_response": raw_result}
        except Exception as e:
            contract["error"] = {"message": str(e), "raw_response": raw_result}

        return contract

    def _parse_model_output(self, raw: str) -> dict:
        # JSON
        first, last = raw.find("{"), raw.rfind("}")
        if first != -1 and last > first:
            try:
                data = json.loads(raw[first:last + 1])
                if isinstance(data, dict):
                    content = data.get("content") or data.get("code") or ""
                    if content:
                        return {
                            "content": str(content).strip(),
                            "explanation": str(data.get("explanation", "")).strip(),
                            "language": str(data.get("language", "lua")).strip() or "lua",
                        }
            except (json.JSONDecodeError, ValueError):
                pass

        # Markdown blocks
        match = self._RE_LUA_BLOCK.search(raw) or self._RE_ANY_BLOCK.search(raw)
        if match:
            return {
                "content": match.group(1).strip(),
                "explanation": self._RE_ANY_BLOCK.sub("", raw).strip(),
                "language": "lua",
            }

        return {"content": raw.strip(), "explanation": "", "language": "lua"}

    @classmethod
    def _strip_lowcode_wrap(cls, content: str) -> str:
        if not content:
            return ""
        m = cls._RE_LOWCODE_WRAP.search(content.strip())
        return m.group(1).strip() if m else content.strip()
