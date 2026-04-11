import json
import time
import os
from openai import OpenAI
from knowledge import get_generator_system_prompt # Импортируем нашу базу знаний

class LocalQwenGenerator:
    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        self.client = OpenAI(
            base_url=base_url,
            api_key="local-hackathon-key",
            timeout=120.0
        )
        
        # 1. Читаем базовый промпт из файла
        prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "generator.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            base_prompt = f.read().strip()
            
        # 2. Обогащаем промпт правилами платформы и примерами
        self.system_prompt = get_generator_system_prompt(base_prompt)

    def generate(self, refined_prompt: str, request_id: str, model_name: str = "qwen2.5:7b") -> dict:
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
                "model": model_name,
                "usage": {
                    "total_tokens": 0,
                    "duration_ms": 0
                }
            },
            "error": None
        }
        
        raw_result = ""
        
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": refined_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
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

if __name__ == "__main__":
    generator = LocalQwenGenerator()
    
    task_from_adapter = "Напиши функцию на Lua, которая принимает таблицу чисел и возвращает их сумму."
    incoming_request_id = "550e8400-e29b-41d4-a716-446655440000"
    
    result = generator.generate(task_from_adapter, request_id=incoming_request_id)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
