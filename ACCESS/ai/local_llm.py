import json
import requests


class LocalLLM:
    def __init__(
        self,
        model="qwen3:1.7b",
        base_url="http://127.0.0.1:11434",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.generate_url = f"{self.base_url}/api/generate"

    def is_available(self):
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=2,
            )
            return response.ok
        except requests.RequestException:
            return False

    def interpret(self, command):
        prompt = f"""
Return ONLY valid JSON.
No explanation.
No markdown.
No thinking.

Command: {command}

JSON format:
{{"intent":"...", "target":"..."}}
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": 32,
            },
        }

        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            text = data.get("response", "").strip()

            return self._parse_json(text)

        except requests.RequestException as exc:
            return {
                "intent": "unknown",
                "target": None,
                "error": str(exc),
            }

    @staticmethod
    def _parse_json(text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting JSON if the model added extra text.
            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass

            return {
                "intent": "unknown",
                "target": None,
                "raw": text,
            }