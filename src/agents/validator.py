import json
import subprocess
import tempfile
import os
import re
import time
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI

# ИМПОРТЫ
from core.config import Config
from knowledge import get_validator_system_prompt # Предполагаем, что такая функция есть для валидатора

# ==========================================
# 1. КОНТРАКТЫ ДАННЫХ ДЛЯ ВНУТРЕННЕЙ ЛОГИКИ
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
    # ПРАВКА: Инициализация по примеру
    def __init__(self, client: OpenAI, model_name: str = Config.MODEL_NAME):
        self.client = client
        self.model_name = model_name

        # Читаем базовый промпт из файла по примеру
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "validator.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                base_prompt = f.read().strip()
        except FileNotFoundError:
            # Фолбэк, если файл не найден
            base_prompt = "Ты Senior Lua Validator. Проверь код на логику и соответствие ТЗ."
            
        # Обогащаем промпт через базу знаний (как в примере)
        self.system_prompt = get_validator_system_prompt(base_prompt)

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

    def validate(self, task: Task, code_result: CodeResult) -> dict:
        """Основной метод, возвращающий результат по контракту"""
        start_time = time.time()
        
        # Инициализация структуры ответа
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
                "model": self.model_name,
                "usage": {
                    "total_tokens": 0,
                    "duration_ms": 0
                }
            },
            "error": None
        }

        try:
            # --- ШАГ 1: Синтаксический анализ ---
            syntax_error = self._run_syntax_check(code_result.code)
            if syntax_error:
                contract["payload"]["issues"].append(f"Syntax error: {syntax_error}")
                contract["payload"]["recommendation"] = "retry"
                contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start_time) * 1000)
                return contract

            # --- ШАГ 2: Семантический анализ через LLM ---
            # ПРАВКА: Используем промпт, загруженный в __init__
            user_prompt = f"ТЗ: {task.original_prompt}\nКод:\n{code_result.code}"

            # ПРАВКА: Параметры из Config
            llm_params = Config.get_llm_params()

            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                **llm_params
            )

            # Парсинг ответа модели с очисткой от Markdown
            raw_result = response.choices[0].message.content.strip()
            if raw_result.startswith("```"):
                raw_result = raw_result.strip("`").strip()
                if raw_result.startswith("json"):
                    raw_result = raw_result[4:].strip()

            llm_res = json.loads(raw_result)
            
            # Обновление контракта
            contract["payload"]["is_valid"] = llm_res.get("is_valid", False)
            contract["payload"]["issues"] = llm_res.get("issues", [])
            contract["payload"]["recommendation"] = llm_res.get("recommendation", "retry")
            
            # Сбор метрик
            if hasattr(response, 'usage') and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = getattr(response.usage, 'total_tokens', 0)
            
            # Детект зацикливания
            if task.iteration >= 3 and not contract["payload"]["is_valid"]:
                contract["payload"]["recommendation"] = "abort"
                contract["payload"]["issues"].append("Max iterations reached. Agent is stuck.")

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
    
    test_task = Task(original_prompt="Напиши сумму", request_id="test-123", iteration=1)
    test_code = CodeResult(code="function sum(a,b) return a + b end", iteration=1)
    
    result = validator.validate(test_task, test_code)
    print(json.dumps(result, indent=2, ensure_ascii=False))
