import json
import time
import uuid
from openai import OpenAI

class LocalQwenAdapter:
    def __init__(self, base_url: str = "http://localhost:11434/v1"):
        self.client = OpenAI(
            base_url=base_url,
            api_key="local-hackathon-key",
            timeout=60.0
        )
        
        self.system_prompt = """
        Ты — AI-адаптер. Принимай сырой запрос пользователя и формируй четкое ТЗ для следующего агента (генератора).
        Возвращай СТРОГИЙ JSON. Никаких рассуждений.
        
        СТРУКТУРА:
        {
            "status": "success" | "clarification",
            "display_text": "Вопрос пользователю или статус готовности",
            "refined_prompt": "Готовое ТЗ для генератора (null, если нужно уточнение)",
            "is_ready": true | false
        }
        
        Если запрос неясен, status = "clarification", is_ready = false, refined_prompt = null.
        """

    def adapt(self, raw_input: str, request_id: str = None, model_name: str = "qwen2.5:7b") -> dict:
        req_id = request_id or str(uuid.uuid4())
        start_time = time.time()
        
        contract = {
            "header": {
                "source_agent": "adapter",
                "request_id": req_id,
                "timestamp": int(start_time),
                "status": "error"
            },
            "payload": {
                "display_text": "",
                "refined_prompt": None,
                "is_ready": False
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
                    {"role": "user", "content": raw_input}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
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
            contract["payload"]["display_text"] = llm_data.get("display_text", "")
            contract["payload"]["refined_prompt"] = llm_data.get("refined_prompt")
            contract["payload"]["is_ready"] = llm_data.get("is_ready", False)
            
            return contract
            
        except json.JSONDecodeError:
            contract["error"] = {"message": "Invalid output format", "raw_response": raw_result}
            return contract
        except Exception as e:
            contract["error"] = {"message": str(e)}
            return contract

if __name__ == "__main__":
    adapter = LocalQwenAdapter()
    
    messy_text = "Сделай мне кнопку для сайта, чтобы красная была"
    incoming_request_id = "550e8400-e29b-41d4-a716-446655440000"
    
    result = adapter.adapt(messy_text, request_id=incoming_request_id)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
