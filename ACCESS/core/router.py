from dataclasses import dataclass
import re


# ============================================================
# INTENT
# ============================================================

@dataclass
class Intent:
    """Represents a detected user intent."""

    name: str
    target: str = ""
    confidence: float = 0.0


# ============================================================
# INTENT ROUTER
# ============================================================

class IntentRouter:
    """Detect user intent from natural-language commands."""

    # --------------------------------------------------------
    # APPLICATION ALIASES
    # --------------------------------------------------------

    APPLICATION_ALIASES = {
        "chrome": "Google Chrome",
        "google chrome": "Google Chrome",

        "calculator": "Calculator",
        "calc": "Calculator",

        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "visual studio code": "Visual Studio Code",

        "terminal": "Terminal",
<<<<<<< HEAD
        "notepad": "Notepad",
        "file explorer": "File Explorer",
        "explorer": "File Explorer",
        "files": "File Explorer",
        "task manager": "Task Manager",
        "taskmgr": "Task Manager",
        "paint": "Paint",
=======

>>>>>>> modification
        "safari": "Safari",

        "finder": "Finder",
    }

    # ========================================================
    # ROUTE
    # ========================================================

    def route(self, user_input: str) -> Intent:
        """Analyze user input and return a structured intent."""

        command = " ".join(
            (user_input or "").strip().split()
        )

        if not command:
            return Intent(
                name="empty",
                confidence=1.0,
            )

        command_lower = command.lower()

        # ====================================================
        # ABOUT / IDENTITY
        # ====================================================

        if command_lower in {
            "who are you",
            "who are you?",
            "what are you",
            "what are you?",
            "introduce yourself",
            "tell me about yourself",
        }:
            return Intent(
                name="about",
                confidence=1.0,
            )

        # ====================================================
        # EXIT
        # ====================================================

        if command_lower in {
            "exit",
            "quit",
            "bye",
            "goodbye",
            "close access",
        }:
            return Intent(
                name="exit",
                confidence=1.0,
            )

        # ====================================================
        # SCREENSHOT
        # ====================================================

        if command_lower in {
            "screenshot",
            "take screenshot",
            "take a screenshot",
            "capture screenshot",
            "capture a screenshot",
        }:
            return Intent(
                name="screenshot",
                confidence=1.0,
            )

        # ====================================================
        # SHUTDOWN
        # ====================================================

        if command_lower in {
            "shutdown",
            "shut down",
            "power off",
            "power off computer",
            "power off the computer",
            "turn off computer",
            "turn off the computer",
        }:
            return Intent(
                name="shutdown",
                confidence=1.0,
            )

        # ====================================================
        # RESTART
        # ====================================================

        if command_lower in {
            "restart",
            "restart computer",
            "restart the computer",
            "reboot",
            "reboot computer",
            "reboot the computer",
        }:
            return Intent(
                name="restart",
                confidence=1.0,
            )

        # ====================================================
        # SLEEP
        # ====================================================

        if command_lower in {
            "sleep",
            "sleep computer",
            "put computer to sleep",
            "put the computer to sleep",
        }:
            return Intent(
                name="sleep",
                confidence=1.0,
            )

        # ====================================================
        # LOCK SCREEN
        # ====================================================

        if command_lower in {
            "lock",
            "lock screen",
            "lock the screen",
            "lock computer",
            "lock the computer",
        }:
            return Intent(
                name="lock_screen",
                confidence=1.0,
            )

        # ====================================================
        # VOLUME UP
        # ====================================================

        if command_lower in {
            "volume up",
            "increase volume",
            "increase the volume",
            "turn volume up",
            "turn the volume up",
            "louder",
        }:
            return Intent(
                name="volume_up",
                confidence=1.0,
            )

        # ====================================================
        # VOLUME DOWN
        # ====================================================

        if command_lower in {
            "volume down",
            "decrease volume",
            "decrease the volume",
            "turn volume down",
            "turn the volume down",
            "lower volume",
            "lower the volume",
            "quieter",
        }:
            return Intent(
                name="volume_down",
                confidence=1.0,
            )

        # ====================================================
        # MUTE
        # ====================================================

        if command_lower in {
            "mute",
            "mute volume",
            "mute sound",
            "mute audio",
        }:
            return Intent(
                name="mute",
                confidence=1.0,
            )

        # ====================================================
        # BRIGHTNESS UP
        # ====================================================

        if command_lower in {
            "brightness up",
            "increase brightness",
            "increase the brightness",
            "turn brightness up",
            "turn the brightness up",
            "brighter",
        }:
            return Intent(
                name="brightness_up",
                confidence=1.0,
            )

        # ====================================================
        # BRIGHTNESS DOWN
        # ====================================================

        if command_lower in {
            "brightness down",
            "decrease brightness",
            "decrease the brightness",
            "turn brightness down",
            "turn the brightness down",
            "lower brightness",
            "lower the brightness",
            "darker",
        }:
            return Intent(
                name="brightness_down",
                confidence=1.0,
            )

        # ====================================================
        # DARK MODE
        # ====================================================

        if command_lower in {
            "dark mode",
            "darkmode",
            "turn on dark mode",
            "turn on darkmode",
            "turn dark mode on",
            "turn darkmode on",
            "enable dark mode",
            "enable darkmode",
            "switch to dark mode",
            "switch to darkmode",
        }:
            return Intent(
                name="dark_mode",
                confidence=1.0,
            )

        # ====================================================
        # LIGHT / WHITE MODE
        # ====================================================

        if command_lower in {
            "light mode",
            "lightmode",
            "white mode",
            "whitemode",

            "turn on light mode",
            "turn on lightmode",
            "turn on white mode",
            "turn on whitemode",

            "turn light mode on",
            "turn lightmode on",
            "turn white mode on",
            "turn whitemode on",

            "enable light mode",
            "enable lightmode",
            "enable white mode",
            "enable whitemode",

            "switch to light mode",
            "switch to lightmode",
            "switch to white mode",
            "switch to whitemode",
        }:
            return Intent(
                name="light_mode",
                confidence=1.0,
            )

        # ====================================================
        # OPEN APPLICATION
        # ====================================================

        open_patterns = [
            r"^open\s+(.+)$",
            r"^launch\s+(.+)$",
            r"^start\s+(.+)$",
        ]

        for pattern in open_patterns:
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
                    name="open_application",
                    target=target,
                    confidence=1.0,
                )

        # ====================================================
        # CLOSE APPLICATION
        # ====================================================

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
                    confidence=1.0,
                )

        # ====================================================
        # CREATE FILE
        # ====================================================

        create_patterns = [
            r"^create\s+file\s+(.+)$",
            r"^create\s+(.+)$",
        ]

        for pattern in create_patterns:
            match = re.match(
                pattern,
                command,
                re.IGNORECASE,
            )

            if match:
                return Intent(
                    name="create_file",
                    target=match.group(1).strip(),
                    confidence=1.0,
                )

        # ====================================================
        # READ FILE
        # ====================================================

        read_patterns = [
            r"^read\s+file\s+(.+)$",
            r"^read\s+(.+)$",
        ]

        for pattern in read_patterns:
            match = re.match(
                pattern,
                command,
                re.IGNORECASE,
            )

            if match:
                return Intent(
                    name="read_file",
                    target=match.group(1).strip(),
                    confidence=1.0,
                )

        # ====================================================
        # DELETE FILE
        # ====================================================

        delete_patterns = [
            r"^delete\s+file\s+(.+)$",
            r"^delete\s+(.+)$",
            r"^remove\s+file\s+(.+)$",
            r"^remove\s+(.+)$",
        ]

        for pattern in delete_patterns:
            match = re.match(
                pattern,
                command,
                re.IGNORECASE,
            )

            if match:
                return Intent(
                    name="delete_file",
                    target=match.group(1).strip(),
                    confidence=1.0,
                )

        # ====================================================
        # SEARCH FILE
        # ====================================================

        search_patterns = [
            r"^search\s+file\s+(.+)$",
            r"^find\s+file\s+(.+)$",
        ]

        for pattern in search_patterns:
            match = re.match(
                pattern,
                command,
                re.IGNORECASE,
            )

            if match:
                return Intent(
                    name="search_file",
                    target=match.group(1).strip(),
                    confidence=1.0,
                )

        # ====================================================
        # COPY FILE
        # ====================================================

        match = re.match(
            r"^copy\s+file\s+(.+?)\s+to\s+(.+)$",
            command,
            re.IGNORECASE,
        )

        if match:
            return Intent(
                name="copy_file",
                target=(
                    f"{match.group(1).strip()}"
                    f"|"
                    f"{match.group(2).strip()}"
                ),
                confidence=1.0,
            )

        # ====================================================
        # MOVE FILE
        # ====================================================

        match = re.match(
            r"^move\s+file\s+(.+?)\s+to\s+(.+)$",
            command,
            re.IGNORECASE,
        )

        if match:
            return Intent(
                name="move_file",
                target=(
                    f"{match.group(1).strip()}"
                    f"|"
                    f"{match.group(2).strip()}"
                ),
                confidence=1.0,
            )

        # ====================================================
        # RENAME FILE
        # ====================================================

        match = re.match(
            r"^rename\s+file\s+(.+?)\s+to\s+(.+)$",
            command,
            re.IGNORECASE,
        )

        if match:
            return Intent(
                name="rename_file",
                target=(
                    f"{match.group(1).strip()}"
                    f"|"
                    f"{match.group(2).strip()}"
                ),
                confidence=1.0,
            )

        # ====================================================
        # UNKNOWN
        # ====================================================

        return Intent(
            name="unknown",
            target=command,
            confidence=0.0,
        )