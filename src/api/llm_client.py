# api/llm_client.py
import logging
from openai import OpenAI
from api.config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Синхронный провайдер клиента OpenAI для Ollama.
    Централизованно управляет подключением, используя настройки из Config.
    """
    def __init__(self):
        # Автоматически подтягиваем URL и Ключ из конфига
        # Это обеспечит работу в Docker (через http://ollama:11434)
        self.client = OpenAI(
            base_url=Config.OLLAMA_URL,
            api_key=Config.API_KEY
        )
        logger.info(f"LLM Client инициализирован для {Config.OLLAMA_URL}")

    def get_instance(self) -> OpenAI:
        """Возвращает настроенный экземпляр OpenAI SDK."""
        return self.client

# Создаем один экземпляр на всё приложение
llm = LLMClient()
