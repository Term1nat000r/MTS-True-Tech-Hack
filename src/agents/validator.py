import json
import subprocess
import tempfile
import os
import time
from typing import List, Optional
from pydantic import BaseModel, Field
from openai import OpenAI
from src.api.config import Config
from src.api.knowledge import get_validator_system_prompt


class Task(BaseModel):
    original_prompt: str
    iteration: int = 1

class CodeResult(BaseModel):
    code: str
    iteration: int


class Validator:
    def __init__(self, client: OpenAI):
        self.client = client
        try:
            with open(Config.PROMPTS_DIR / "validator.txt", "r", encoding="utf-8") as f:
                base_prompt = f.read().strip()
        except FileNotFoundError:
            base_prompt = "Ты Senior Lua Validator. Проверь код на логику и соответствие ТЗ."
        self.system_prompt = get_validator_system_prompt(base_prompt)

    @staticmethod
    def _strip_wrapper(code: str) -> str:
        return code.replace("jsonString lua{", "").replace("}lua", "").strip()

    def _run_syntax_check(self, lua_code: str) -> Optional[str]:
        fd, path = tempfile.mkstemp(suffix=".lua")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(lua_code)
            result = subprocess.run(['luac', '-p', path], capture_output=True, text=True, timeout=5)
            return None if result.returncode == 0 else result.stderr.replace(path, "line").strip()
        except FileNotFoundError:
            return None  # luac not installed — skip syntax check
        except Exception as e:
            return None  # don't block on system errors
        finally:
            if os.path.exists(path):
                os.remove(path)

    def validate(self, task: Task, code_result: CodeResult) -> dict:
        start = time.time()
        contract = {
            "header": {"source_agent": "validator", "timestamp": int(start), "status": "success"},
            "payload": {"is_valid": False, "issues": [], "recommendation": "retry"},
            "metadata": {"model": Config.MODEL_NAME, "usage": {"total_tokens": 0, "duration_ms": 0}},
            "error": None,
        }

        try:
            clean_code = self._strip_wrapper(code_result.code)

            # Syntax check on clean Lua (without wrapper)
            syntax_error = self._run_syntax_check(clean_code)
            if syntax_error:
                contract["payload"]["issues"].append(f"Syntax error: {syntax_error}")
                contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start) * 1000)
                return contract

            # LLM logic review
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"ТЗ: {task.original_prompt}\nПроверь только этот Lua код:\n{clean_code}"},
                ],
                **Config.get_llm_params(),
            )
            if hasattr(response, "usage") and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = getattr(response.usage, "total_tokens", 0)

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.strip("`").strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()

            llm_res = json.loads(raw)
            contract["payload"]["is_valid"] = llm_res.get("is_valid", False)
            contract["payload"]["issues"] = llm_res.get("issues", [])

            if contract["payload"]["is_valid"]:
                contract["payload"]["recommendation"] = "pass"
            elif task.iteration >= 3:
                contract["payload"]["recommendation"] = "abort"
                contract["payload"]["issues"].append("Max iterations reached.")

        except Exception as e:
            contract["header"]["status"] = "error"
            contract["error"] = {"message": str(e)}
            contract["payload"]["recommendation"] = "abort"

        contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start) * 1000)
        return contract
