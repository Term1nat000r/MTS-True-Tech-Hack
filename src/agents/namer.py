from openai import OpenAI
from src.api.config import Config


class Namer:
    def __init__(self, client: OpenAI):
        self.client = client
        with open(Config.PROMPTS_DIR / "namer.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()

    def generate_name(self, raw_input: str) -> str:
        try:
            params = Config.get_llm_params()
            params.pop("response_format", None)
            response = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": raw_input}
                ],
                **params
            )
            name = response.choices[0].message.content.strip().strip('"').strip("'")
            return name if name else "Новый диалог"
        except Exception as e:
            print(f"[Namer Error] LLM упала: {e}")
            return "Новый диалог"
