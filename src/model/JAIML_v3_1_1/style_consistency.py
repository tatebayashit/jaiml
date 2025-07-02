
from typing import Optional
import openai
import os
import logging
import re

logger = logging.getLogger(__name__)

class StyleConsistencyEvaluator:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI APIキーが未設定")
        openai.api_key = self.api_key
        self.model = model

    def evaluate(self, context: str, response: str, prompt_template: str) -> float:
        prompt = f"""{prompt_template}

[文脈]: {context}
[応答]: {response}"""
        try:
            result = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたは文体一貫性の評価者です。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            reply = result["choices"][0]["message"]["content"].strip().lower()
            if re.search(r"\byes\b", reply) and not re.search(r"\bbut\b|\bhowever\b", reply):
                return 1.0
            elif re.search(r"\bno\b", reply):
                return 0.0
            else:
                return 0.5
        except Exception as e:
            logger.warning(f"GPT呼び出し失敗: {e}")
            return 0.5
