import json
import time
import os
import re
from openai import OpenAI
 
from src.api.knowledge import get_generator_system_prompt
from src.api.config import Config
 
 
class Generator:
    """
    Агент-генератор Lua-кода для платформы MTS LowCode.
 
    Возвращает контракт с двумя представлениями кода в payload:
        - content:  как требует платформа — "jsonString lua{ ... }lua"
        - lua_code: чистое тело обёртки, удобное для валидатора/критика
    """
 
    _RE_LUA_BLOCK = re.compile(r"```lua\s*(.*?)```", re.DOTALL | re.IGNORECASE)
    _RE_ANY_BLOCK = re.compile(r"```[a-zA-Z0-9_+-]*\s*(.*?)```", re.DOTALL)
    _RE_LOWCODE_WRAP = re.compile(
        r"jsonString\s+lua\s*\{(.*)\}\s*lua\s*$",
        re.DOTALL | re.IGNORECASE,
    )
 
    def __init__(self, client: OpenAI):
        self.client = client
        prompt_path = Config.PROMPTS_DIR / "generator.txt"
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
        self.system_prompt = get_generator_system_prompt(base_prompt)
 
    def generate(self, refined_prompt: str, request_id: str) -> dict:
        start_time = time.time()
        contract = self._empty_contract(request_id, start_time)
 
        raw_result = ""
        try:
            llm_params = Config.get_llm_params()
 
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": refined_prompt},
                ],
                **llm_params,
            )
 
            duration_ms = int((time.time() - start_time) * 1000)
            contract["metadata"]["usage"]["duration_ms"] = duration_ms
 
            if hasattr(response, "usage") and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = getattr(
                    response.usage, "total_tokens", 0
                )
 
            if not response.choices or not response.choices[0].message.content:
                contract["error"] = {"message": "Empty response from model"}
                return contract
 
            raw_result = response.choices[0].message.content.strip()
            parsed = self._parse_model_output(raw_result)
 
            content_for_platform = parsed["content"]
            lua_code = self._strip_lowcode_wrap(content_for_platform)
 
            contract["header"]["status"] = "success"
            contract["payload"]["content"] = content_for_platform
            contract["payload"]["lua_code"] = lua_code
            contract["payload"]["explanation"] = parsed["explanation"]
            contract["payload"]["language"] = parsed["language"]
 
            if not content_for_platform.strip():
                contract["header"]["status"] = "error"
                contract["error"] = {
                    "message": "Could not extract Lua code from model output",
                    "raw_response": raw_result,
                }
 
            return contract
 
        except json.JSONDecodeError:
            contract["error"] = {
                "message": "Invalid output format",
                "raw_response": raw_result,
            }
            return contract
        except Exception as e:
            contract["error"] = {
                "message": str(e),
                "raw_response": raw_result,
                "exception_type": type(e).__name__,
            }
            return contract
 
    def _parse_model_output(self, raw: str) -> dict:
        """Трёхуровневое извлечение кода. Никогда не бросает исключений."""
 
        # Уровень 1: JSON
        json_candidate = self._extract_json_blob(raw)
        if json_candidate is not None:
            try:
                data = json.loads(json_candidate)
                if isinstance(data, dict):
                    # Поддерживаем оба имени поля на случай, если модель
                    # назвала его "code" вместо "content".
                    content = data.get("content") or data.get("code") or ""
                    if content:
                        return {
                            "content": str(content).strip(),
                            "explanation": str(data.get("explanation", "")).strip(),
                            "language": str(data.get("language", "lua")).strip() or "lua",
                        }
            except (json.JSONDecodeError, ValueError):
                pass
 
        # Уровень 2: markdown-блоки
        match = self._RE_LUA_BLOCK.search(raw)
        if match:
            return {
                "content": match.group(1).strip(),
                "explanation": self._strip_code_blocks(raw).strip(),
                "language": "lua",
            }
 
        match = self._RE_ANY_BLOCK.search(raw)
        if match:
            return {
                "content": match.group(1).strip(),
                "explanation": self._strip_code_blocks(raw).strip(),
                "language": "lua",
            }
 
        # Уровень 3: fallback
        return {
            "content": raw.strip(),
            "explanation": "",
            "language": "lua",
        }
 
    @staticmethod
    def _extract_json_blob(text: str) -> str | None:
        first = text.find("{")
        last = text.rfind("}")
        if first == -1 or last == -1 or last <= first:
            return None
        return text[first : last + 1]
 
    @classmethod
    def _strip_code_blocks(cls, text: str) -> str:
        return cls._RE_ANY_BLOCK.sub("", text)
 
    @classmethod
    def _strip_lowcode_wrap(cls, content: str) -> str:
        """Достать чистый Lua из обёртки jsonString lua{ ... }lua."""
        if not content:
            return ""
        m = cls._RE_LOWCODE_WRAP.search(content.strip())
        return m.group(1).strip() if m else content.strip()
 
    @staticmethod
    def _empty_contract(request_id: str, start_time: float) -> dict:
        return {
            "header": {
                "source_agent": "generator",
                "request_id": request_id,
                "timestamp": int(start_time),
                "status": "error",
            },
            "payload": {
                "content": "",       # формат платформы: jsonString lua{...}lua
                "lua_code": "",      # чистый Lua для валидатора/критика
                "explanation": "",
                "language": "lua",
            },
            "metadata": {
                "model": Config.MODEL_NAME,
                "usage": {
                    "total_tokens": 0,
                    "duration_ms": 0,
                },
            },
            "error": None,
        }
 
 
if __name__ == "__main__":
    test_client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="local-hackathon-key",
    )
    generator = Generator(client=test_client)
 
    task_from_adapter = "Напиши функцию на Lua, которая принимает таблицу чисел и возвращает их сумму."
    incoming_request_id = "550e8400-e29b-41d4-a716-446655440000"
 
    result = generator.generate(task_from_adapter, request_id=incoming_request_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
