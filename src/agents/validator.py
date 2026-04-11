import json
import subprocess
import tempfile
import os
import re
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI

# ==========================================
# 1. КОНТРАКТЫ ДАННЫХ
# ==========================================
class Task(BaseModel):
    original_prompt: str
    request_id: str
    iteration: int = 1
    history_comments: List[str] = Field(default_factory=list)

class CodeResult(BaseModel):
    code: str
    iteration: int

# ==========================================
# 2. АГЕНТ 3: ВАЛИДАТОР (Validator Agent)
# ==========================================

class CriticAgent:
    def __init__(self, client: OpenAI):
        self.client = client
        
        # Считываем системный промпт из файла validator.txt
        # Путь строится относительно расположения этого файла
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_path = os.path.join(current_dir, "prompts", "validator.txt")
        
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.system_prompt = f.read().strip()
        except FileNotFoundError:
            # Резервный промпт на случай, если файл не найден
            self.system_prompt = "Ты Senior Lua Validator. Проверяй код и возвращай JSON."
            print(f"ВНИМАНИЕ: Файл {prompt_path} не найден! Использован резервный промпт.")

    def _run_syntax_check(self, code: str) -> Optional[str]:
        """Статическая проверка через luac -p"""
        fd, temp_path = tempfile.mkstemp(suffix=".lua")
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(code)
            result = subprocess.run(['luac', '-p', temp_path], capture_output=True, text=True, timeout=5)
            return None if result.returncode == 0 else result.stderr.replace(temp_path, "line").strip()
        except Exception as e:
            return f"System error during syntax check: {str(e)}"
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def validate(self, task: Task, code_result: CodeResult, model_name: str = "qwen2.5:7b") -> dict:
        start_time = time.time()
        
        # Инициализация контракта
        contract = {
            "header": {
                "source_agent": "validator",
                "request_id": task.request_id,
                "timestamp": int(start_time),
                "status": "success"
            },
            "payload": {
                "is_valid": False,
                "issues": [],
                "recommendation": "retry"
            },
            "metadata": {
                "model": model_name,
                "usage": {"total_tokens": 0, "duration_ms": 0}
            },
            "error": None
        }

        try:
            # 1. Синтаксический анализ (Fast Fail)
            syntax_error = self._run_syntax_check(code_result.code)
            if syntax_error:
                contract["payload"]["issues"].append(f"Syntax error: {syntax_error}")
                contract["payload"]["recommendation"] = "retry"
                contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start_time) * 1000)
                return contract

            # 2. Семантический анализ через LLM
            user_prompt = f"ТЗ пользователя:\n{task.original_prompt}\n\nСгенерированный код:\n{code_result.code}"

            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # Парсинг ответа
            llm_data = json.loads(response.choices[0].message.content)
            
            contract["payload"]["is_valid"] = llm_data.get("is_valid", False)
            contract["payload"]["issues"] = llm_data.get("issues", [])
            contract["payload"]["recommendation"] = llm_data.get("recommendation", "retry")
            
            # Собираем метрики
            if hasattr(response, 'usage') and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = response.usage.total_tokens

            # Детект зацикливания
            if task.iteration >= 3 and not contract["payload"]["is_valid"]:
                contract["payload"]["recommendation"] = "abort"
                contract["payload"]["issues"].append("Превышено макс. число итераций исправления.")

            if contract["payload"]["is_valid"]:
                contract["payload"]["recommendation"] = "pass"

        except Exception as e:
            contract["header"]["status"] = "error"
            contract["error"] = {"message": str(e)}
            contract["payload"]["recommendation"] = "abort"

        contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start_time) * 1000)
        return contract

# Блок для локального тестирования
if __name__ == "__main__":
    test_client = OpenAI(base_url="http://localhost:11434/v1", api_key="local-hackathon-key")
    validator = CriticAgent(client=test_client)
    
    t = Task(original_prompt="Напиши функцию суммы", request_id="12345")
    c = CodeResult(code="function sum(a,b) return a+b end", iteration=1)
    
    res = validator.validate(t, c)
    print(json.dumps(res, indent=2, ensure_ascii=False))
