import json
import time
import os
from openai import OpenAI
from knowledge import get_generator_system_prompt # Импортируем нашу базу знаний
from core.config import Config

class LocalQwenGenerator:
    # ПРАВКА: Принимаем готовый клиент извне
    def __init__(self, client: OpenAI):
        self.client = client
        
        # Читаем базовый промпт из файла
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "generator.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
            
        # Обогащаем промпт правилами платформы и примерами
        self.system_prompt = get_generator_system_prompt(base_prompt)

    def generate(self, refined_prompt: str, request_id: str) -> dict:
        start_time = time.time()
        
        contract = {
            "header": {
                "source_agent": "generator",
                "request_id": request_id,
                "timestamp": int(start_time),
                "status": "error"
            },
            "payload": {
                "content": "",
                "explanation": "",
                "language": "lua"
            },
            "metadata": {
                "model": Config.MODEL_NAME,
                "usage": {
                    "total_tokens": 0,
                    "duration_ms": 0
                }
            },
            "error": None
        }
        
        raw_result = ""
        
        try:
            llm_params = Config.get_llm_params()
    
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": refined_prompt}
                ],
                **llm_params
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            contract["metadata"]["usage"]["duration_ms"] = duration_ms
            
            if hasattr(response, 'usage') and response.usage:
                contract["metadata"]["usage"]["total_tokens"] = getattr(response.usage, 'total_tokens', 0)

            if not response.choices or not response.choices[0].message.content:
                contract["error"] = {"message": "Empty response from model"}
                return contract
                
            raw_result = response.choices[0].message.content.strip()
            
            if raw_result.startswith("```"):
                raw_result = raw_result.strip("`").strip()
                if raw_result.startswith("json"):
                    raw_result = raw_result[4:].strip()
            
            llm_data = json.loads(raw_result)
            
            contract["header"]["status"] = llm_data.get("status", "success")
            contract["payload"]["content"] = llm_data.get("content", "")
            contract["payload"]["explanation"] = llm_data.get("explanation", "")
            contract["payload"]["language"] = llm_data.get("language", "lua")
            
            return contract
            
        except json.JSONDecodeError:
            contract["error"] = {"message": "Invalid output format", "raw_response": raw_result}
            return contract
        except Exception as e:
            contract["error"] = {"message": str(e)}
            return contract

# ПРАВКА: Блок для локального тестирования файла
if __name__ == "__main__":
    # Создаем тестового клиента
    test_client = OpenAI(base_url="http://localhost:11434/v1", api_key="local-hackathon-key")
    generator = LocalQwenGenerator(client=test_client)
    
    task_from_adapter = "Напиши функцию на Lua, которая принимает таблицу чисел и возвращает их сумму."
    incoming_request_id = "550e8400-e29b-41d4-a716-446655440000"
    
    result = generator.generate(task_from_adapter, request_id=incoming_request_id)
    print(json.dumps(result, indent=2, ensure_ascii=False))
