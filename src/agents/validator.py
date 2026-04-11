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
    def __init__(self, client: OpenAI, model_name: str = "qwen2.5:7b"):
        self.client = client
        self.model_name = model_name

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
        
        # Инициализация структуры ответа (Контракт)
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
            system_prompt = (
                "Ты Senior Lua Validator. Проверь код на логику и соответствие ТЗ.\n"
                "Отвечай ТОЛЬКО в формате JSON: {\"is_valid\": bool, \"issues\": [], \"recommendation\": \"retry\"|\"pass\"|\"abort\"}"
            )
            user_prompt = f"ТЗ: {task.original_prompt}\nКод:\n{code_result.code}"

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )

            # Парсинг ответа модели
            llm_res = json.loads(response.choices[0].message.content)
            
            # Обновление контракта данными из LLM
            contract["payload"]["is_valid"] = llm_res.get("is_valid", False)
            contract["payload"]["issues"] = llm_res.get("issues", [])
            contract["payload"]["recommendation"] = llm_res.get("recommendation", "retry")
            
            # Сбор метрик
            contract["metadata"]["usage"]["total_tokens"] = getattr(response.usage, 'total_tokens', 0)
            
            # Детект зацикливания (если итераций слишком много)
            if task.iteration >= 3 and not contract["payload"]["is_valid"]:
                contract["payload"]["recommendation"] = "abort"
                contract["payload"]["issues"].append("Max iterations reached. Agent is stuck.")

            # Если всё ок
            if contract["payload"]["is_valid"]:
                contract["payload"]["recommendation"] = "pass"

        except Exception as e:
            contract["header"]["status"] = "error"
            contract["error"] = {"message": str(e)}
            contract["payload"]["recommendation"] = "abort"

        contract["metadata"]["usage"]["duration_ms"] = int((time.time() - start_time) * 1000)
        return contract
