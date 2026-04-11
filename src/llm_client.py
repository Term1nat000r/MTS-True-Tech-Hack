import time
import logging
from typing import Type, TypeVar, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError
from ollama import AsyncClient, ResponseError

T_Payload = TypeVar('T_Payload', bound=BaseModel)

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Продвинутая обертка над Ollama API, адаптированная под контракты.
    Берет на себя сборку сообщений, замеры времени, извлечение usage-метрик 
    и строгую валидацию payload-части контракта.
    """
    def __init__(self, host: str = "http://localhost:11434"):
        self.client = AsyncClient(host=host)

    async def execute_agent_task(
        self,
        system_prompt: str,
        agent_input: Dict[str, Any], # Приходит agentInput_contract в виде словаря или Pydantic-модели
        expected_payload_class: Type[T_Payload]
    ) -> Tuple[T_Payload, Dict[str, int]]:
        """
        Отправляет задачу в модель и возвращает готовый Payload + метрики (usage).
        """
        # 1. Распаковка конфигурации из agentInput_contract
        config = agent_input.get("agent_config", {})
        model_name = config.get("model", "qwen2.5:7b") # Дефолт из твоих контрактов
        parameters = config.get("parameters", {"temperature": 0.5})
        
        # 2. Сборка контекста (история + новый запрос)
        data = agent_input.get("data", {})
        messages = [{"role": "system", "content": system_prompt}]
        
        # Подтягиваем историю, если она есть
        if "history" in data and data["history"]:
            messages.extend(data["history"])
            
        # Добавляем текущую задачу/промпт
        if "input_text" in data and data["input_text"]:
            messages.append({"role": "user", "content": data["input_text"]})

        logger.info(f"Запуск агента [{config.get('target', 'unknown')}] на модели {model_name}")

        # Засекаем время для metadata.duration_ms
        start_time = time.time()

        try:
            # 3. Вызов Ollama
            response = await self.client.chat(
                model=model_name,
                messages=messages,
                format='json',
                options=parameters
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            raw_content = response['message']['content']
            
            # 4. Валидация ТОЛЬКО части payload
            validated_payload = expected_payload_class.model_validate_json(raw_content)
            
            # 5. Сбор метрик для metadata.usage
            usage_metrics = {
                "total_tokens": response.get("eval_count", 0) + response.get("prompt_eval_count", 0),
                "duration_ms": duration_ms
            }
            
            return validated_payload, usage_metrics

        except ResponseError as e:
            logger.error(f"Ошибка Ollama API: {e}")
            raise
        except ValidationError as e:
            logger.error(f"Модель сломала JSON-контракт Payload:\n{e}")
            raise
        except Exception as e:
            logger.error(f"Критическая ошибка в LLMClient: {e}")
            raise

llm = LLMClient()
