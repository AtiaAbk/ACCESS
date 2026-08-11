"""
ACCESS Intent Router

Converts natural-language user commands into structured intents.
"""

from dataclasses import dataclass
import re


@dataclass
class Intent:
    """Represents a detected user intent."""

    name: str
    target: str = ""
    confidence: float = 0.0


class IntentRouter:
    """Detect user intent from natural-language commands."""

    APPLICATION_ALIASES = {
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",
        "calculator": "Calculator",
        "calc": "Calculator",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "visual studio code": "Visual Studio Code",
        "terminal": "Terminal",
        "safari": "Safari",
        "finder": "Finder",
    }

    def route(self, user_input: str) -> Intent:
        """Analyze user input and return a structured intent."""

        command = user_input.strip()

        if not command:
            return Intent(
                name="empty",
                confidence=1.0,
            )

        command_lower = command.lower()

        # --------------------------------------------------
        # EXIT
        # --------------------------------------------------

        if command_lower in {
            "exit",
            "quit",
            "bye",
            "goodbye",
        }:
            return Intent(
                name="exit",
                confidence=1.0,
            )

        # --------------------------------------------------
        # OPEN APPLICATION
        # --------------------------------------------------

        open_patterns = [
            r"^open\s+(.+)$",
            r"^launch\s+(.+)$",
            r"^start\s+(.+)$",
            close_patterns = [
    r"^close\s+(.+)$",
    r"^quit\s+(.+)$",
    r"^stop\s+(.+)$",
]

for pattern in close_patterns:
    match = re.match(
        pattern,
        command,
        re.IGNORECASE,
    )

    if match:
        target = match.group(1).strip()

        target = self.APPLICATION_ALIASES.get(
            target.lower(),
            target,
        )

        return Intent(
            name="close_application",
            target=target,
            confidence=0.95,
        )
        ]

        for pattern in open_patterns:
            match = re.match(pattern, command, re.IGNORECASE)

            if match:
                target = match.group(1).strip()

                target = self.APPLICATION_ALIASES.get(
                    target.lower(),
                    target,
                )

                return Intent(
                    name="open_application",
                    target=target,
                    confidence=0.95,
                )

        # --------------------------------------------------
        # UNKNOWN
        # --------------------------------------------------

        return Intent(
            name="unknown",
            target=command,
            confidence=0.0,
        )

