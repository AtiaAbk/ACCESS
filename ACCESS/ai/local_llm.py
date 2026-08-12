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
You are the command interpreter for ACCESS, an intelligent desktop assistant.

Return ONLY valid JSON.
No markdown.
No explanation.
No thinking.

Classify the user's command into one of these intents:

- open_application
- close_application
- create_file
- read_file
- delete_file
- search_file
- copy_file
- move_file
- rename_file
- screenshot
- lock_screen
- volume_up
- volume_down
- mute
- brightness_up
- brightness_down
- shutdown
- restart
- sleep
- exit
- conversation
- unknown

For system commands, use:
{{"intent":"intent_name","target":"target"}}

For normal conversation such as hello, hi, thanks, etc., use:
{{"intent":"conversation","target":"","response":"short natural response"}}

For unknown commands use:
{{"intent":"unknown","target":"command"}}

User command:
{command}
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0,
                "num_predict": 48,
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
                "target": command,
                "error": str(exc),
            }

    @staticmethod
    def _parse_json(text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")

            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end + 1])
                except json.JSONDecodeError:
                    pass

            return {
                "intent": "unknown",
                "target": text,
            }