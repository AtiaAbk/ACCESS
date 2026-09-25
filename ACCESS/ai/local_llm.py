import json
import urllib.error
import urllib.request

try:
    import requests
except ModuleNotFoundError:
    requests = None


class LocalLLM:
    """
    Local Ollama-based language model interface.

    Used for:
    - Natural conversation
    - General questions
    - Mathematics
    - Multilingual interaction
    - Command interpretation fallback
    """

    def __init__(
        self,
        model="qwen3:1.7b",
        base_url="http://127.0.0.1:11434",
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")

        self.generate_url = (
            f"{self.base_url}/api/generate"
        )

    def is_available(self):
        if requests is not None:
            try:
                response = requests.get(
                    f"{self.base_url}/api/tags",
                    timeout=2,
                )
                return response.ok
            except Exception:
                return False

        try:
            req = urllib.request.Request(
                f"{self.base_url}/api/tags",
                headers={"User-Agent": "ACCESS/2.0"},
            )
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def interpret(self, command):

        prompt = f"""
You are ACCESS, a friendly intelligent desktop assistant.

You are not a robotic command parser.

Return ONLY valid JSON.
Never return markdown.

Classify the user's request.

Allowed intents:

open_application
close_application
create_file
read_file
delete_file
search_file
copy_file
move_file
rename_file
screenshot
lock_screen
volume_up
volume_down
mute
brightness_up
brightness_down
dark_mode
light_mode
shutdown
restart
sleep
set_alarm
set_reminder
current_time
current_date
conversation
unknown

For system actions:

{{"intent":"open_application","target":"Calculator"}}

For conversation:

{{"intent":"conversation","target":"","response":"natural response"}}

Conversation behavior:

- Be friendly.
- Be concise but intelligent.
- You may joke lightly.
- Never pretend that you performed an action you did not perform.
- Answer normal questions naturally.
- Handle mathematics.
- Understand different languages.
- Match the user's language when practical.
- Do not sound robotic.

User:
{command}
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 128,
            },
        }

        try:
            if requests is not None:
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=15,
                )
                response.raise_for_status()
                data = response.json()
            else:
                req = urllib.request.Request(
                    self.generate_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ACCESS/2.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

            text = data.get(
                "response",
                "",
            ).strip()

            return self._parse_json(text)

        except Exception as exc:

            return {
                "intent": "unknown",
                "target": command,
                "error": str(exc),
            }

    def chat(self, message):

        """
        Generate a natural conversational response.
        """

        prompt = f"""
You are ACCESS, a friendly local desktop AI assistant.

Personality:
- intelligent
- calm
- witty
- friendly
- slightly playful
- never annoying
- never overly verbose
- helpful like a good personal assistant

Answer the user naturally.

Rules:
- Do not claim to have performed an action unless the application actually executed it.
- If the user asks a normal question, answer it.
- Solve basic mathematics accurately.
- Understand multilingual questions.
- If you do not know something, say so honestly.
- Keep simple answers concise.
- For complex questions, explain clearly.

User:
{message}

Assistant:
"""

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.65,
                "num_predict": 256,
            },
        }

        try:
            if requests is not None:
                response = requests.post(
                    self.generate_url,
                    json=payload,
                    timeout=20,
                )
                response.raise_for_status()
                data = response.json()
            else:
                req = urllib.request.Request(
                    self.generate_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "ACCESS/2.0"},
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

            return data.get(
                "response",
                "",
            ).strip()

        except Exception:
            return None

    @staticmethod
    def _parse_json(text):

        try:
            return json.loads(text)

        except json.JSONDecodeError:

            start = text.find("{")
            end = text.rfind("}")

            if (
                start != -1
                and end != -1
                and end > start
            ):

                try:
                    return json.loads(
                        text[start:end + 1]
                    )

                except json.JSONDecodeError:
                    pass

            return {
                "intent": "unknown",
                "target": text,
            }