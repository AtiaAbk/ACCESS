import re


class GoalDetector:
    """
    Detects intent + target from natural language
    with a confidence score.
    """

    PATTERNS = [
        # -------------------------------------------------
        # APPLICATION CONTROL
        # -------------------------------------------------

        (
            "open_application",
            r"\bopen\s+(.+)",
            0.90,
        ),
        (
            "close_application",
            r"\bclose\s+(.+)",
            0.90,
        ),

        # -------------------------------------------------
        # SYSTEM CONTROL
        # -------------------------------------------------

        (
            "shutdown",
            r"\bshut\s*down\b",
            0.95,
        ),
        (
            "restart",
            r"\brestart\b",
            0.95,
        ),
        (
            "sleep",
            r"\bsleep\b",
            0.90,
        ),
        (
            "lock_screen",
            r"\block\s+(?:the\s+)?screen\b|\block\s+computer\b|\block\s+pc\b",
            0.90,
        ),

        # -------------------------------------------------
        # TIME / DATE
        # -------------------------------------------------

        (
            "get_time",
            r"\b(?:what(?:'s| is)?\s+)?(?:the\s+)?(?:current\s+)?time(?:\s+is\s+it)?\b"
            r"|\btime\s+(?:is\s+it|now)\b"
            r"|\bcurrent\s+time\b"
            r"|\bwhat\s+time\s+is\s+it\b",
            0.95,
        ),

        (
            "get_date",
            r"\b(?:what(?:'s| is)?\s+)?(?:today'?s?\s+)?date(?:\s+is\s+it)?\b"
            r"|\bcurrent\s+date\b"
            r"|\bwhat\s+date\s+is\s+it\b"
            r"|\bwhat\s+day\s+is\s+(?:it|today)\b"
            r"|\bwhat\s+day\s+today\b",
            0.95,
        ),

        # -------------------------------------------------
        # SCREENSHOT
        # -------------------------------------------------

        (
            "screenshot",
            r"\btake\s+(?:a\s+)?screenshot\b"
            r"|\bscreenshot\b"
            r"|\bcapture\s+(?:the\s+)?screen\b"
            r"|\bcapture\s+screen\b",
            0.90,
        ),

        # -------------------------------------------------
        # FILE OPERATIONS
        # -------------------------------------------------

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
            r"\bfind\s+(?:the\s+)?file\s+(.+)"
            r"|\bsearch\s+(?:for\s+)?(.+)",
            0.80,
        ),
        (
            "copy_file",
            r"\bcopy\s+(?:the\s+)?file\s+(.+)",
            0.85,
        ),
        (
            "move_file",
            r"\bmove\s+(?:the\s+)?file\s+(.+)",
            0.85,
        ),
        (
            "rename_file",
            r"\brename\s+(?:the\s+)?file\s+(.+)",
            0.85,
        ),
    ]

    # -----------------------------------------------------
    # LEADING FILLER
    # -----------------------------------------------------

    LEADING_FILLER = (
        r"^(?:"
        r"could you|"
        r"can you|"
        r"would you|"
        r"will you|"
        r"please|"
        r"i want to|"
        r"i need to|"
        r"i'd like to|"
        r"hey|"
        r"kindly"
        r")\s+"
    )

    # -----------------------------------------------------
    # TRAILING FILLER
    # -----------------------------------------------------

    TRAILING_FILLER = (
        r"\s*"
        r"(?:for me|please|now|thanks|thank you)?"
        r"\s*[?!.]*\s*$"
    )

    # -----------------------------------------------------
    # TITLE CASE TARGETS
    # -----------------------------------------------------

    TITLE_CASE_INTENTS = {
        "open_application",
        "close_application",
    }

    # -----------------------------------------------------
    # DETECTION
    # -----------------------------------------------------

    def detect(self, text: str):
        """
        Return:

            (intent, target, confidence)

        Unknown commands return:

            ("unknown", None, 0.0)
        """

        original_cleaned = (
            (text or "")
            .strip()
            .lower()
        )

        if not original_cleaned:
            return "unknown", None, 0.0

        # ---------------------------------------------
        # Remove leading conversational filler
        # ---------------------------------------------

        stripped = re.sub(
            self.LEADING_FILLER,
            "",
            original_cleaned,
            count=1,
        ).strip()

        # ---------------------------------------------
        # Check patterns
        # ---------------------------------------------

        for (
            intent,
            pattern,
            base_confidence,
        ) in self.PATTERNS:

            match = re.search(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            target = None

            # -----------------------------------------
            # Extract first non-empty capture group
            # -----------------------------------------

            for group in match.groups():

                if group:

                    target = group.strip()

                    break

            # -----------------------------------------
            # Clean target
            # -----------------------------------------

            if target:

                target = re.sub(
                    self.TRAILING_FILLER,
                    "",
                    target,
                ).strip()

                target = re.sub(
                    r"^(?:the|a|an)\s+",
                    "",
                    target,
                ).strip()

                if (
                    intent
                    in self.TITLE_CASE_INTENTS
                    and target
                ):

                    target = " ".join(
                        word.capitalize()
                        for word in target.split()
                    )

            # -----------------------------------------
            # Confidence
            # -----------------------------------------

            confidence = base_confidence

            command_verb = intent.split("_")[0]

            if stripped.startswith(command_verb):

                confidence = min(
                    confidence + 0.05,
                    1.0,
                )

            return (
                intent,
                target,
                confidence,
            )

        # ---------------------------------------------
        # Unknown
        # ---------------------------------------------

        return (
            "unknown",
            None,
            0.0,
        )