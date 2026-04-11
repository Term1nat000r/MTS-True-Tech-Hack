import os
from pathlib import Path

class Config:
    # --- ИНФРАСТРУКТУРА ---
    # Получаем путь к папке проекта
    BASE_DIR = Path(__file__).resolve().parent
    
    # Пытаемся взять URL из настроек системы (getenv), 
    # если платформа её передаст. Если нет — используем твой локальный URL.
    OLLAMA_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434/v1")
    
    # Ключ тоже лучше прописать так, на случай если на платформе 
    # решат использовать не Ollama, а прокси к GPT-4
    API_KEY = os.getenv("LLM_API_KEY", "local-hackathon-key")


    # --- ТРЕБОВАНИЯ ПЛАТФОРМЫ (ОГРАНИЧЕНИЯ) ---
    # Qwen2.5:7b занимает ~4.7GB - 5.5GB VRAM. 
    # Лимит 8GB позволяет запускать модель и оставлять запас под контекст.
    VRAM_LIMIT_GB = 8 
    
    # Лимиты токенов (согласно требованиям к платформе)
    # Суммарный контекст (вход + выход)
    CONTEXT_WINDOW = 4096 
    # Лимит на один ответ (чтобы не превышать время генерации)
    MAX_TOKENS_PER_RESPONSE = 1024 

    # --- НАСТРОЙКИ МОДЕЛИ ---
    MODEL_NAME = "qwen2.5:7b"
    TEMPERATURE = 0.1  # Фиксируем для стабильности JSON в контрактах
    SEED = 42          # Для детерминированности ответов

    # --- НАСТРОЙКИ ОРКЕСТРАТОРА ---
    # Максимальное количество попыток исправления кода Валидатором
    MAX_VALIDATION_ITERATIONS = 3 
    # Тайм-аут на один запрос к LLM (в секундах)
    REQUEST_TIMEOUT = 120.0

    # --- КОНТРАКТЫ (Имена агентов и статусы) ---
    # Используем эти константы в коде, чтобы не было опечаток в JSON
    AGENTS = {
        "ADAPTER": "refiner",      # Он же Clarifier
        "GENERATOR": "generator",
        "VALIDATOR": "validator"
    }
    
    STATUSES = {
        "SUCCESS": "success",
        "ERROR": "error",
        "CLARIFY": "clarification"
    }

    #RECOMMENDATIONS = {
        "RETRY": "retry",
        "PASS": "pass",
        "ABORT": "abort"
    }

    # --- ПЕРЕМЕННЫЕ ДЛЯ МЕТРИК (Будущее расширение) ---
    # Эти ключи будут использоваться в блоке "metadata" каждого контракта
    METRIC_KEYS = [
        "total_tokens",
        "duration_ms",
        "vram_usage_mb",  # Планируем отслеживать потребление памяти
        "iteration_index"
    ]

    @classmethod
    def get_llm_params(cls):
        """Метод для получения стандартного набора параметров для всех агентов"""
        return {
            "model": cls.MODEL_NAME,
            "temperature": cls.TEMPERATURE,
            "max_tokens": cls.MAX_TOKENS_PER_RESPONSE,
            "seed": cls.SEED,
            "extra_body": {
                "num_ctx": cls.CONTEXT_WINDOW
            }
        }

# Создаем базовые директории при импорте конфига
(Config.BASE_DIR / "logs").mkdir(exist_ok=True)
(Config.BASE_DIR / "prompts").mkdir(exist_ok=True)
