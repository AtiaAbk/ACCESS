import re


class GoalDetector:
    """
    Detect intent and target from natural-language commands.

    This layer does NOT execute anything.
    It only converts language into structured intent.
    """

    PATTERNS = [
        # Applications
        (
            "open_application",
            r"\b(?:open|launch|start)\s+(.+)",
            0.90,
        ),
        (
            "close_application",
            r"\b(?:close|quit|stop)\s+(.+)",
            0.90,
        ),

        # System
        (
            "shutdown",
            r"\b(?:shut\s*down|power\s*off)\b",
            0.95,
        ),
        (
            "restart",
            r"\b(?:restart|reboot)\b",
            0.95,
        ),
        (
            "sleep",
            r"\b(?:put\s+(?:the\s+)?computer\s+to\s+sleep|sleep)\b",
            0.90,
        ),
        (
            "lock_screen",
            r"\b(?:lock\s+(?:the\s+)?screen|lock\s+(?:the\s+)?computer)\b",
            0.90,
        ),

        # Screenshot
        (
            "screenshot",
            r"\b(?:take\s+(?:a\s+)?screenshot|capture\s+(?:the\s+)?screen|screenshot)\b",
            0.95,
        ),

        # Audio
        (
            "volume_up",
            r"\b(?:volume\s+up|increase\s+volume|turn\s+volume\s+up|louder)\b",
            0.90,
        ),
        (
            "volume_down",
            r"\b(?:volume\s+down|decrease\s+volume|turn\s+volume\s+down|quieter)\b",
            0.90,
        ),
        (
            "mute",
            r"\b(?:mute|mute\s+volume|mute\s+sound)\b",
            0.95,
        ),

        # Brightness
        (
            "brightness_up",
            r"\b(?:brightness\s+up|increase\s+brightness|turn\s+brightness\s+up|brighter)\b",
            0.90,
        ),
        (
            "brightness_down",
            r"\b(?:brightness\s+down|decrease\s+brightness|turn\s+brightness\s+down|darker)\b",
            0.90,
        ),

        # Files
        (
            "create_file",
            r"\bcreate\s+(?:a\s+)?file\s+(.+)",
            0.85,
        ),
        (
            "read_file",
            r"\bread\s+(?:the\s+)?file\s+(.+)",
            0.85,
        ),
        (
            "delete_file",
            r"\bdelete\s+(?:the\s+)?file\s+(.+)",
            0.85,
        ),
        (
            "search_file",
            r"\b(?:find|search)\s+(?:for\s+)?(?:the\s+)?file\s+(.+)",
            0.85,
        ),
        (
            "copy_file",
            r"\bcopy\s+file\s+(.+?)\s+to\s+(.+)",
            0.85,
        ),
        (
            "move_file",
            r"\bmove\s+file\s+(.+?)\s+to\s+(.+)",
            0.85,
        ),
        (
            "rename_file",
            r"\brename\s+file\s+(.+?)\s+to\s+(.+)",
            0.85,
        ),

        # Dark/light mode
        (
            "dark_mode",
            r"\b(?:turn\s+on|enable|switch\s+to)\s+(?:dark\s+mode|dark\s+theme)\b",
            0.90,
        ),
        (
            "light_mode",
            r"\b(?:turn\s+on|enable|switch\s+to)\s+(?:light\s+mode|white\s+mode|light\s+theme)\b",
            0.90,
        ),

        # Time/date
        (
            "current_time",
            r"\b(?:what\s+(?:is|s)\s+the\s+time|what\s+time\s+is\s+it|current\s+time|time\s+now)\b",
            0.98,
        ),
        (
            "current_date",
            r"\b(?:what\s+(?:is|s)\s+(?:the\s+)?date|today'?s\s+date|what\s+day\s+is\s+today)\b",
            0.98,
        ),

        # Reminder / alarm
        (
            "set_reminder",
            r"\b(?:set|create|make)\s+(?:a\s+)?reminder\b(.+)?",
            0.90,
        ),
        (
            "set_alarm",
            r"\b(?:set|create)\s+(?:an\s+)?alarm\b(.+)?",
            0.90,
        ),
    ]

    LEADING_FILLER = re.compile(
        r"^(?:could you|can you|would you|will you|"
        r"please|i want to|i need to|i'd like to|"
        r"hey|kindly|jarvis|access)\s+",
        re.IGNORECASE,
    )

    TRAILING_FILLER = re.compile(
        r"\s*(?:for me|please|now|thanks|thank you)"
        r"\s*[?!.]*\s*$",
        re.IGNORECASE,
    )

    TITLE_CASE_INTENTS = {
        "open_application",
        "close_application",
    }

    APPLICATION_ALIASES = {
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",
        "calculator": "Calculator",
        "calc": "Calculator",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "visual studio code": "Visual Studio Code",
        "code": "Visual Studio Code",
        "terminal": "Terminal",
        "safari": "Safari",
        "finder": "Finder",
        "notes": "Notes",
    }

    def detect(self, text: str):
        """
        Return:

            (intent, target, confidence)
        """

        original = (text or "").strip()

        if not original:
            return "unknown", None, 0.0

        stripped = self.LEADING_FILLER.sub(
            "",
            original,
            count=1,
        ).strip()

        for intent, pattern, confidence in self.PATTERNS:

            match = re.search(
                pattern,
                stripped,
                re.IGNORECASE,
            )

            if not match:
                continue

            target = None

            for group in match.groups():
                if group:
                    target = group.strip()
                    break

            if target:
                target = self.TRAILING_FILLER.sub(
                    "",
                    target,
                ).strip()

                target = re.sub(
                    r"^(?:the|a|an)\s+",
                    "",
                    target,
                    flags=re.IGNORECASE,
                ).strip()

            if intent in self.TITLE_CASE_INTENTS and target:

                target_lower = target.lower()

                target = self.APPLICATION_ALIASES.get(
                    target_lower,
                    " ".join(
                        word.capitalize()
                        for word in target.split()
                    ),
                )

            return intent, target, confidence

        return "unknown", None, 0.0