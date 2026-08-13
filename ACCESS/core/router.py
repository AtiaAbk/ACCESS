"""
ACCESS Intent Router
--------------------
Deterministic command parser for ACCESS.

Design goal:
- Normal sentences are NOT treated as commands.
- Explicit system commands are detected reliably.
- Commands can appear inside polite/natural-language prompts.
- Multiple explicit commands separated by "then" / "and then" can be
  returned by route_all().
"""

from dataclasses import dataclass
import re


@dataclass
class Intent:
    name: str
    target: str = ""
    confidence: float = 0.0


class IntentRouter:
    """Detect explicit desktop commands without hijacking normal chat."""

    APPLICATION_ALIASES = {
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",
        "calculator": "Calculator",
        "calc": "Calculator",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "visual studio code": "Visual Studio Code",
        "terminal": "Terminal",
        "notepad": "Notepad",
        "file explorer": "File Explorer",
        "explorer": "File Explorer",
        "files": "File Explorer",
        "task manager": "Task Manager",
        "taskmgr": "Task Manager",
        "paint": "Paint",
        "safari": "Safari",
        "finder": "Finder",
    }

    _POLITE_PREFIX = re.compile(
        r"^(?:please|kindly|can you|could you|would you|"
        r"would you please|can you please|could you please)\s+",
        re.I,
    )

    _SYSTEM_COMMANDS = {
        "screenshot": "screenshot",
        "take screenshot": "screenshot",
        "take a screenshot": "screenshot",
        "capture screenshot": "screenshot",
        "capture a screenshot": "screenshot",

        "shutdown": "shutdown",
        "shut down": "shutdown",
        "power off": "shutdown",
        "power off computer": "shutdown",
        "power off the computer": "shutdown",
        "turn off computer": "shutdown",
        "turn off the computer": "shutdown",

        "restart": "restart",
        "restart computer": "restart",
        "restart the computer": "restart",
        "reboot": "restart",
        "reboot computer": "restart",
        "reboot the computer": "restart",

        "sleep": "sleep",
        "sleep computer": "sleep",
        "put computer to sleep": "sleep",
        "put the computer to sleep": "sleep",

        "lock": "lock_screen",
        "lock screen": "lock_screen",
        "lock the screen": "lock_screen",
        "lock computer": "lock_screen",
        "lock the computer": "lock_screen",

        "volume up": "volume_up",
        "increase volume": "volume_up",
        "increase the volume": "volume_up",
        "turn volume up": "volume_up",
        "turn the volume up": "volume_up",
        "louder": "volume_up",

        "volume down": "volume_down",
        "decrease volume": "volume_down",
        "decrease the volume": "volume_down",
        "turn volume down": "volume_down",
        "turn the volume down": "volume_down",
        "lower volume": "volume_down",
        "lower the volume": "volume_down",
        "quieter": "volume_down",

        "mute": "mute",
        "mute volume": "mute",
        "mute sound": "mute",
        "mute audio": "mute",

        "brightness up": "brightness_up",
        "increase brightness": "brightness_up",
        "increase the brightness": "brightness_up",
        "turn brightness up": "brightness_up",
        "turn the brightness up": "brightness_up",
        "brighter": "brightness_up",

        "brightness down": "brightness_down",
        "decrease brightness": "brightness_down",
        "decrease the brightness": "brightness_down",
        "turn brightness down": "brightness_down",
        "turn the brightness down": "brightness_down",
        "lower brightness": "brightness_down",
        "lower the brightness": "brightness_down",
        "darker": "brightness_down",

        "dark mode": "dark_mode",
        "darkmode": "dark_mode",
        "turn on dark mode": "dark_mode",
        "turn on darkmode": "dark_mode",
        "turn dark mode on": "dark_mode",
        "turn darkmode on": "dark_mode",
        "enable dark mode": "dark_mode",
        "enable darkmode": "dark_mode",
        "switch to dark mode": "dark_mode",
        "switch to darkmode": "dark_mode",

        "light mode": "light_mode",
        "lightmode": "light_mode",
        "white mode": "light_mode",
        "whitemode": "light_mode",
        "turn on light mode": "light_mode",
        "turn on lightmode": "light_mode",
        "turn on white mode": "light_mode",
        "turn on whitemode": "light_mode",
        "turn light mode on": "light_mode",
        "turn lightmode on": "light_mode",
        "turn white mode on": "light_mode",
        "turn whitemode on": "light_mode",
        "enable light mode": "light_mode",
        "enable lightmode": "light_mode",
        "enable white mode": "light_mode",
        "enable whitemode": "light_mode",
        "switch to light mode": "light_mode",
        "switch to lightmode": "light_mode",
        "switch to white mode": "light_mode",
        "switch to whitemode": "light_mode",
    }

    _EXACT_SPECIAL = {
        "who are you": "about",
        "what are you": "about",
        "introduce yourself": "about",
        "tell me about yourself": "about",
        "exit": "exit",
        "quit": "exit",
        "bye": "exit",
        "goodbye": "exit",
        "close access": "exit",
    }

    def _clean(self, text: str) -> str:
        text = " ".join((text or "").strip().split())
        text = self._POLITE_PREFIX.sub("", text).strip()
        return text.rstrip("?!.,").strip()

    def route_all(self, user_input: str) -> list[Intent]:
        """
        Return every explicit command in a prompt.

        We only split on strong command separators ("then", "and then",
        semicolon/newline). This prevents ordinary conversation containing
        the word "and" from being accidentally split into commands.
        """
        text = " ".join((user_input or "").strip().split())
        if not text:
            return [Intent(name="empty", confidence=1.0)]

        parts = re.split(r"\s+(?:and\s+then|then)\s+|[;\n]+", text, flags=re.I)
        intents = []

        for part in parts:
            part = part.strip()
            if not part:
                continue
            intent = self.route(part)
            if intent.name != "unknown":
                intents.append(intent)

        return intents

    def route(self, user_input: str) -> Intent:
        command = self._clean(user_input)

        if not command:
            return Intent("empty", confidence=1.0)

        lower = command.casefold()

        # Exact special commands only.
        if lower in self._EXACT_SPECIAL:
            return Intent(self._EXACT_SPECIAL[lower], confidence=1.0)

        # Exact known system commands.
        if lower in self._SYSTEM_COMMANDS:
            return Intent(self._SYSTEM_COMMANDS[lower], confidence=1.0)

        # A command can be embedded after a short natural-language prefix.
        # We deliberately require command-like verbs/phrases.
        normalized = re.sub(r"^[,:-]+\s*", "", lower)

        # Application open/close.
        match = re.search(
            r"\b(?:open|launch|start)\s+(.+?)(?=\s+(?:and\s+then|then)\s+|[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            target = match.group(1).strip()
            target = self.APPLICATION_ALIASES.get(target.casefold(), target)
            return Intent("open_application", target, 1.0)

        match = re.search(
            r"\b(?:close|quit|stop)\s+(.+?)(?=\s+(?:and\s+then|then)\s+|[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            target = match.group(1).strip()
            target = self.APPLICATION_ALIASES.get(target.casefold(), target)
            return Intent("close_application", target, 1.0)

        # File operations require the explicit word "file" for safety.
        match = re.search(
            r"\bcreate\s+(?:a\s+)?file\s+(.+?)(?=\s+(?:and\s+then|then)\s+|[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent("create_file", match.group(1).strip(), 1.0)

        match = re.search(
            r"\bread\s+(?:the\s+)?file\s+(.+?)(?=\s+(?:and\s+then|then)\s+|[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent("read_file", match.group(1).strip(), 1.0)

        match = re.search(
            r"\b(?:delete|remove)\s+(?:the\s+)?file\s+(.+?)(?=\s+(?:and\s+then|then)\s+|[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent("delete_file", match.group(1).strip(), 1.0)

        match = re.search(
            r"\b(?:search|find)\s+(?:for\s+)?(?:the\s+)?file\s+(.+?)(?=\s+(?:and\s+then|then)\s+|[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent("search_file", match.group(1).strip(), 1.0)

        match = re.search(
            r"\bcopy\s+(?:the\s+)?file\s+(.+?)\s+to\s+(.+?)(?:[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent(
                "copy_file",
                f"{match.group(1).strip()}|{match.group(2).strip()}",
                1.0,
            )

        match = re.search(
            r"\bmove\s+(?:the\s+)?file\s+(.+?)\s+to\s+(.+?)(?:[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent(
                "move_file",
                f"{match.group(1).strip()}|{match.group(2).strip()}",
                1.0,
            )

        match = re.search(
            r"\brename\s+(?:the\s+)?file\s+(.+?)\s+to\s+(.+?)(?:[,!?;]|$)",
            normalized,
            re.I,
        )
        if match:
            return Intent(
                "rename_file",
                f"{match.group(1).strip()}|{match.group(2).strip()}",
                1.0,
            )

        # For short system commands embedded in a prompt, require a command
        # phrase plus a command-like cue. This avoids hijacking statements
        # such as "How does dark mode work?"
        cue = re.search(
            r"\b(?:please|can you|could you|would you|"
            r"turn|increase|decrease|enable|disable|switch|"
            r"put|make|set|take|capture|lock|mute|unmute)\b",
            normalized,
            re.I,
        )
        if cue:
            for phrase, intent_name in sorted(
                self._SYSTEM_COMMANDS.items(),
                key=lambda item: len(item[0]),
                reverse=True,
            ):
                if re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", normalized, re.I):
                    return Intent(intent_name, confidence=1.0)

        return Intent("unknown", target=command, confidence=0.0)
