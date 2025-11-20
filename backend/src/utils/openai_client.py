from openai import OpenAI
from typing import List

class OpenAIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def chat(self, messages: List[dict], model: str = "gpt-3.5-turbo") -> str:
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=messages,
            )
            return completion.choices[0].message.content
        except Exception as exc:
            print("OpenAI error:", exc)
            return ""