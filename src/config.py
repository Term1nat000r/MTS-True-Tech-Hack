import os
from pathlib import Path

class Config:
    # --- ИНФРАСТРУКТУРА ---
    BASE_DIR = Path(__file__).resolve().parent
    OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1")
    API_KEY = os.getenv("LLM_API_KEY", "local-hackathon-key")
    
    # Директории
    LOGS_DIR = BASE_DIR / "logs"
    PROMPTS_DIR = BASE_DIR / "prompts"

    # --- ТРЕБОВАНИЯ ПЛАТФОРМЫ ---
    VRAM_LIMIT_GB = 8 
    CONTEXT_WINDOW = 4096 
    MAX_TOKENS_PER_RESPONSE = 1024
    REQUEST_TIMEOUT = 120.0

    # --- НАСТРОЙКИ МОДЕЛИ ---
    MODEL_NAME = "qwen2.5:7b"
    TEMPERATURE = 0.1
    SEED = 42
    
    # Sampling (Точность)
    TOP_K = 40
    TOP_P = 0.9
    MIN_P = 0.05
    
    # Penalties (Борьба с циклами)
    REPEAT_PENALTY = 1.1
    
    # Формат ответа
    RESPONSE_FORMAT = {"type": "json_object"}

    # --- НАСТРОЙКИ АГЕНТОВ ---
    MAX_VALIDATION_ITERATIONS = 3
    RETRY_ATTEMPTS = 2
    RETRY_DELAY_SEC = 1.0

    # --- ИМЕНА КОНТРАКТОВ (Constants) ---
    AGENTS = {
        "ADAPTER": "refiner",
        "GENERATOR": "generator",
        "VALIDATOR": "validator"
    }
    
    STATUSES = {
        "SUCCESS": "success",
        "ERROR": "error",
        "CLARIFY": "clarification"
    }

    RECOMMENDATIONS = {
        "RETRY": "retry",
        "PASS": "pass",
        "ABORT": "abort"
    }

    # --- МЕТРИКИ (Будущее) ---
    METRIC_KEYS = [
        "total_tokens",
        "duration_ms",
        "vram_usage_mb",
        "iteration_index"
    ]

    @classmethod
    def get_llm_params(cls):
        """Метод возвращает словарь параметров для вызова LLM"""
        return {
            "model": cls.MODEL_NAME,
            "temperature": cls.TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS_PER_RESPONSE,
            "seed": cls.SEED,
            "response_format": cls.RESPONSE_FORMAT,
            "extra_body": {
                "num_ctx": cls.CONTEXT_WINDOW,
                "top_k": cls.TOP_K,
                "top_p": cls.TOP_P,
                "min_p": cls.MIN_P,
                "repeat_penalty": cls.REPEAT_PENALTY
            }
        }

# Создаем папки автоматически
Config.LOGS_DIR.mkdir(exist_ok=True)
Config.PROMPTS_DIR.mkdir(exist_ok=True)
