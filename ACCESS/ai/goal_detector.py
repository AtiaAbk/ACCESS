import re


class GoalDetector:
    """Detects intent + target from natural language with a confidence score."""

    PATTERNS = [
        ("open_application", r"\bopen\s+(.+)", 0.9),
        ("close_application", r"\bclose\s+(.+)", 0.9),
        ("shutdown", r"\bshut\s*down\b", 0.95),
        ("restart", r"\brestart\b", 0.95),
        ("sleep", r"\bsleep\b", 0.9),
        ("screenshot", r"\bscreenshot\b|\bcapture\s+screen\b", 0.9),
        ("create_file", r"\bcreate\s+(?:a\s+)?file\s+(.+)", 0.85),
        ("read_file", r"\bread\s+(?:the\s+)?file\s+(.+)", 0.85),
        ("delete_file", r"\bdelete\s+(?:the\s+)?file\s+(.+)", 0.85),
        ("search_file", r"\bfind\s+(?:the\s+)?file\s+(.+)|\bsearch\s+(?:for\s+)?(.+)", 0.8),
    ]

    # Leading politeness/filler that should be stripped before matching so
    # "Could you open X" is treated the same as "open X".
    LEADING_FILLER = (
        r"^(could you|can you|would you|will you|please|i want to|"
        r"i need to|i'd like to|hey|kindly)\s+"
    )

    # Trailing filler that leaks into a captured target if left in.
    TRAILING_FILLER = (
        r"\s*(for me|please|now|thanks|thank you)?\s*[?!.]*\s*$"
    )

    # Intents whose target is an application/file name we want cleanly cased.
    TITLE_CASE_INTENTS = {"open_application", "close_application"}

    def detect(self, text: str):
        """Return (intent, target, confidence) — falls back to unknown."""
        original_cleaned = text.strip().lower()

        # Strip polite/filler prefixes so intent verbs at the "real" start
        # of the request are recognized as such.
        stripped = re.sub(self.LEADING_FILLER, "", original_cleaned, count=1).strip()

        for intent, pattern, base_confidence in self.PATTERNS:
            match = re.search(pattern, stripped)
            if match:
                target = None
                for group in match.groups():
                    if group:
                        target = group.strip()
                        break

                if target:
                    target = re.sub(self.TRAILING_FILLER, "", target).strip()
                    target = re.sub(r"^(the|a|an)\s+", "", target).strip()
                    if intent in self.TITLE_CASE_INTENTS and target:
                        target = " ".join(w.capitalize() for w in target.split())

                confidence = base_confidence
                if stripped.startswith(intent.split("_")[0]):
                    confidence = min(confidence + 0.05, 1.0)

                return intent, target, confidence

        return "unknown", None, 0.0