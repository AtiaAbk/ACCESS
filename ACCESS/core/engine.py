import os
import platform
import shutil
import subprocess

from pathlib import Path
from datetime import datetime

from ai.decision_engine import AIDecisionEngine
from ai.local_llm import LocalLLM
from core.router import IntentRouter
from memory.database import MemoryDatabase
from tools.system_tools import SystemControl


# ============================================================
# ACCESS ENGINE
# ============================================================

class AccessEngine:
    """
    Central execution engine for ACCESS.

    Responsibilities:
    - Deterministic command routing
    - AI decision layer
    - Local LLM fallback
    - Natural conversation
    - General question answering
    - System control
    - Application control
    - File operations
    - Screenshot capture
    - Multi-step execution
    - Confirmation handling
    - Local memory
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):

        # ----------------------------------------------------
        # CORE COMPONENTS
        # ----------------------------------------------------

        self.router = IntentRouter()

        self.ai = AIDecisionEngine()

        self.local_llm = LocalLLM()

        self.system = SystemControl()

        self.memory = MemoryDatabase()

        # Compatibility alias
        self.system_tools = self.system

        # ----------------------------------------------------
        # ENGINE STATE
        # ----------------------------------------------------

        self.running = True

        self.pending_action = None

        # ----------------------------------------------------
        # CONFIRMATION ACTIONS
        # ----------------------------------------------------

        self.confirmation_actions = {
            "shutdown",
            "restart",
            "sleep",
        }

        # ----------------------------------------------------
        # CONVERSATIONAL INTENTS
        # ----------------------------------------------------

        self.conversational_intents = {
            "conversation",
            "chat",
            "question",
        }

        # ----------------------------------------------------
        # NON-DESTRUCTIVE QUESTION PREFIXES
        #
        # These are used only as a lightweight fallback when
        # the deterministic router and AI decision layer do
        # not identify an executable system task.
        # ----------------------------------------------------

        self.question_prefixes = (
            "what ",
            "what's ",
            "whats ",
            "who ",
            "why ",
            "how ",
            "when ",
            "where ",
            "which ",
            "can you ",
            "could you ",
            "do you ",
            "is ",
            "are ",
            "tell me ",
            "explain ",
            "calculate ",
            "solve ",
        )

    # ========================================================
    # MAIN PROCESSOR
    # ========================================================

    def process(self, user_input: str) -> str:
        """
        Process one user command.

        Processing priority:

            User Input
                 ↓
            Confirmation
                 ↓
            Deterministic Router
                 ↓
            AI Decision Engine
                 ↓
            Local LLM
                 ↓
            Natural conversation / question
                 ↓
            Permission-aware fallback
        """

        command = (user_input or "").strip()

        # ----------------------------------------------------
        # EMPTY COMMAND
        # ----------------------------------------------------

        if not command:
            return "Please enter a command."

        # ----------------------------------------------------
        # DATE / TIME / DAY
        # ----------------------------------------------------

        datetime_response = self._handle_datetime_query(command)

        if datetime_response is not None:

            self._save_memory(
                command,
                datetime_response,
            )

            return datetime_response

        # ----------------------------------------------------
        # PENDING CONFIRMATION
        # ----------------------------------------------------

        if self.pending_action is not None:

            response = self._handle_confirmation(command)

            self._save_memory(
                command,
                response,
            )

            return response

        # ====================================================
        # DETERMINISTIC ROUTER FIRST
        # ====================================================

        intent = self.router.route(command)

        if intent.name != "unknown":

            response = self._execute_intent(
                intent.name,
                intent.target,
            )

            self._save_memory(
                command,
                response,
            )

            return response

        # ====================================================
        # AI DECISION ENGINE
        # ====================================================

        recent_memory = self.get_recent_memory(8)

        try:

            ai_result = self.ai.interpret(
                command,
                recent_memory=recent_memory,
            )

        except Exception:

            ai_result = None

        # ====================================================
        # AI RESULT
        # ====================================================

        if ai_result is not None:

            # ------------------------------------------------
            # MULTI-STEP PLAN
            # ------------------------------------------------

            if (
                ai_result.intent == "multi_step_plan"
                and ai_result.steps
                and ai_result.confidence
                >= self.ai.CONFIDENCE_THRESHOLD
            ):

                response = self._execute_plan(
                    ai_result.steps
                )

                self._save_memory(
                    command,
                    response,
                )

                return response

            # ------------------------------------------------
            # CONVERSATIONAL AI RESULT
            # ------------------------------------------------

            if (
                ai_result.intent
                in self.conversational_intents
            ):

                response = self._ask_local_llm(
                    command
                )

                if response:

                    self._save_memory(
                        command,
                        response,
                    )

                    return response

            # ------------------------------------------------
            # SINGLE AI INTENT
            # ------------------------------------------------

            if (
                ai_result.intent
                and ai_result.intent != "unknown"
                and ai_result.confidence
                >= self.ai.CONFIDENCE_THRESHOLD
            ):

                response = self._execute_intent(
                    ai_result.intent,
                    ai_result.target,
                )

                self._save_memory(
                    command,
                    response,
                )

                return response

        # ====================================================
        # LOCAL LLM
        # ====================================================

        local_result = self._local_llm_interpret(
            command
        )

        if local_result is not None:

            local_intent = (
                local_result.get(
                    "intent",
                    "unknown",
                )
                or "unknown"
            ).strip().lower()

            local_target = (
                local_result.get(
                    "target",
                    "",
                )
                or ""
            ).strip()

            local_response = (
                local_result.get(
                    "response",
                    "",
                )
                or ""
            ).strip()

            # ------------------------------------------------
            # CONVERSATION
            # ------------------------------------------------

            if local_intent in self.conversational_intents:

                if local_response:

                    response = local_response

                else:

                    response = self._ask_local_llm(
                        command
                    )

                if response:

                    self._save_memory(
                        command,
                        response,
                    )

                    return response

            # ------------------------------------------------
            # SYSTEM / APPLICATION / FILE INTENT
            # ------------------------------------------------

            if local_intent != "unknown":

                response = self._execute_intent(
                    local_intent,
                    local_target,
                )

                self._save_memory(
                    command,
                    response,
                )

                return response

        # ====================================================
        # DIRECT LOCAL LLM CHAT FALLBACK
        #
        # This is important for:
        #
        # "What is recursion?"
        # "2 + 2"
        # "Explain TCP"
        # "Who are you?"
        #
        # We don't classify these as system commands.
        # The local model answers naturally.
        # ====================================================

        if self._looks_like_question(command):

            response = self._ask_local_llm(
                command
            )

            if response:

                self._save_memory(
                    command,
                    response,
                )

                return response

        # ====================================================
        # FINAL FAILURE
        # ====================================================

        response = (
            "Sorry, I don't have permission "
            "to access or perform that task."
        )

        self._save_memory(
            command,
            response,
        )

        return response

    # ========================================================
    # LOCAL LLM INTERPRETATION
    # ========================================================

    def _local_llm_interpret(
        self,
        command: str,
    ):
        """
        Safely ask the local LLM to classify a command.

        Returns:
            dict | None
        """

        try:

            if not self.local_llm.is_available():
                return None

            result = self.local_llm.interpret(
                command
            )

            if not isinstance(result, dict):
                return None

            return result

        except Exception:

            return None

    # ========================================================
    # LOCAL LLM CHAT
    # ========================================================

    def _ask_local_llm(
        self,
        command: str,
    ) -> str:
        """
        Ask the local model for a natural conversational
        answer.

        This method intentionally keeps system execution
        separate from general conversation.
        """

        try:

            if not self.local_llm.is_available():
                return ""

            # ------------------------------------------------
            # Use a dedicated chat method if the LocalLLM
            # implementation provides one.
            # ------------------------------------------------

            chat_method = getattr(
                self.local_llm,
                "chat",
                None,
            )

            if callable(chat_method):

                result = chat_method(
                    command,
                    recent_memory=self.get_recent_memory(8),
                )

                if isinstance(result, dict):

                    response = (
                        result.get("response")
                        or result.get("text")
                        or ""
                    )

                    return str(
                        response
                    ).strip()

                if result:

                    return str(
                        result
                    ).strip()

            # ------------------------------------------------
            # Current LocalLLM only exposes interpret().
            #
            # Its "conversation" response can still be used
            # as a compatibility fallback.
            # ------------------------------------------------

            result = self.local_llm.interpret(
                command
            )

            if not isinstance(result, dict):
                return ""

            response = (
                result.get("response")
                or ""
            )

            return str(
                response
            ).strip()

        except Exception:

            return ""

    # ========================================================
    # QUESTION DETECTION
    # ========================================================

    def _looks_like_question(
        self,
        command: str,
    ) -> bool:
        """
        Lightweight check for normal questions/chat.

        This is NOT an AI classifier. It simply prevents
        obviously conversational requests from immediately
        receiving a permission error.
        """

        text = command.strip().lower()

        if not text:
            return False

        # Mathematical expressions
        if self._looks_like_math(text):
            return True

        # Explicit question mark
        if "?" in text:
            return True

        # Common natural-language question starts
        for prefix in self.question_prefixes:

            if text.startswith(prefix):
                return True

        # Common conversational expressions
        conversation_phrases = {
            "hello",
            "hi",
            "hey",
            "hello access",
            "hi access",
            "hey access",
            "good morning",
            "good afternoon",
            "good evening",
            "good night",
            "thanks",
            "thank you",
            "who are you",
            "what can you do",
            "how are you",
            "tell me a joke",
            "make me laugh",
        }

        return text in conversation_phrases

    # ========================================================
    # BASIC MATH DETECTION
    # ========================================================

    @staticmethod
    def _looks_like_math(
        text: str,
    ) -> bool:
        """
        Detect simple mathematical input.

        Actual mathematical reasoning is delegated to the
        local LLM rather than using unsafe eval().
        """

        if not text:
            return False

        allowed = set(
            "0123456789"
            "+-*/().%^ "
        )

        # Pure arithmetic expression
        if all(
            character in allowed
            for character in text
        ):

            return any(
                operator in text
                for operator in (
                    "+",
                    "-",
                    "*",
                    "/",
                    "%",
                    "^",
                )
            )

        math_words = (
            "calculate",
            "solve",
            "equation",
            "plus",
            "minus",
            "times",
            "divided",
            "square root",
            "percentage",
            "percent",
        )

        return any(
            word in text.lower()
            for word in math_words
        )

    # ========================================================
    # DATE / TIME / DAY
    # ========================================================

    def _handle_datetime_query(self, command: str):
        """
        Handle basic date, time and day questions locally.
        This does not depend on the LLM, so ACCESS can answer
        time/date questions even when Ollama is unavailable.
        """

        text = command.strip().lower()

        # Normalize common variations
        normalized = (
            text
            .replace("today's", "todays")
            .replace("what's", "what is")
            .replace("whats", "what is")
            .replace("current", "current")
        )

        time_phrases = (
            "what time is it",
            "what is the time",
            "what is current time",
            "what is the current time",
            "tell me the time",
            "tell me current time",
            "tell me the current time",
            "current time",
            "time now",
            "what time",
        )

        date_phrases = (
            "what is today's date",
            "what is todays date",
            "what is the date",
            "what is today's date today",
            "tell me today's date",
            "tell me todays date",
            "tell me the date",
            "current date",
            "today's date",
            "todays date",
        )

        day_phrases = (
            "what day is today",
            "what day is it",
            "what day is today",
            "tell me what day it is",
            "tell me the day",
            "which day is today",
            "what is the day today",
        )

        # TIME
        if any(phrase in normalized for phrase in time_phrases):

            now = datetime.now()

            return (
                f"It's {now.strftime('%I:%M:%S %p')}."
            )

        # DATE
        if any(phrase in normalized for phrase in date_phrases):

            now = datetime.now()

            return (
                f"Today is {now.strftime('%B %d, %Y')}."
            )

        # DAY
        if any(phrase in normalized for phrase in day_phrases):

            now = datetime.now()

            return (
                f"Today is {now.strftime('%A')}."
            )

        return None

    # ========================================================
    # INTENT EXECUTION
    # ========================================================

    def _execute_intent(
        self,
        intent_name: str,
        target: str = "",
    ) -> str:
        """Execute one structured intent."""

        intent_name = (
            intent_name or ""
        ).strip().lower()

        target = target or ""

        # ----------------------------------------------------
        # EMPTY
        # ----------------------------------------------------

        if intent_name == "empty":

            return "Please enter a command."

        # ----------------------------------------------------
        # UNKNOWN
        # ----------------------------------------------------

        if intent_name == "unknown":

            return (
                "Sorry, I don't have permission "
                "to access or perform that task."
            )

        # ----------------------------------------------------
        # ABOUT
        # ----------------------------------------------------

        if intent_name == "about":

            return (
                "I'm ACCESS — your Adaptive Cognitive "
                "Companion for Efficient System Services.\n"
                "Think of me as your local-first desktop "
                "assistant: I can chat, understand commands, "
                "and help automate your system."
            )

        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        if intent_name == "exit":

            self.running = False

            return "Session terminated safely."

        # ----------------------------------------------------
        # DANGEROUS ACTIONS
        # ----------------------------------------------------

        if intent_name in self.confirmation_actions:

            return self._request_confirmation(
                intent_name
            )

        # ====================================================
        # SYSTEM CONTROL
        # ====================================================

        if intent_name == "lock_screen":

            return self.system.lock_screen()

        if intent_name == "volume_up":

            return self.system.volume_up()

        if intent_name == "volume_down":

            return self.system.volume_down()

        if intent_name == "mute":

            return self.system.mute()

        if intent_name == "brightness_up":

            return self.system.brightness_up()

        if intent_name == "brightness_down":

            return self.system.brightness_down()

        # ----------------------------------------------------
        # DARK MODE
        # ----------------------------------------------------

        if intent_name == "dark_mode":

            return self.system.dark_mode()

        # ----------------------------------------------------
        # LIGHT MODE
        # ----------------------------------------------------

        if intent_name == "light_mode":

            return self.system.light_mode()

        # ====================================================
        # TIME / DATE
        # ====================================================

        if intent_name == "get_time":

            return self._get_current_time()

        if intent_name == "get_date":

            return self._get_current_date()

        # ====================================================
        # APPLICATION CONTROL
        # ====================================================

        if intent_name == "open_application":

            return self.system.open_application(
                self._normalize_application(
                    target
                )
            )

        if intent_name == "close_application":

            return self.system.close_application(
                self._normalize_application(
                    target
                )
            )

        # ====================================================
        # SCREENSHOT
        # ====================================================

        if intent_name == "screenshot":

            return self._handle_screenshot()

        # ====================================================
        # FILE OPERATIONS
        # ====================================================

        if intent_name == "create_file":

            return self._handle_file_operation(
                "create",
                target,
            )

        if intent_name == "read_file":

            return self._handle_file_operation(
                "read",
                target,
            )

        if intent_name == "delete_file":

            return self._handle_file_operation(
                "delete",
                target,
            )

        if intent_name == "search_file":

            return self._handle_file_operation(
                "search",
                target,
            )

        if intent_name == "copy_file":

            return self._handle_file_operation(
                "copy",
                target,
            )

        if intent_name == "move_file":

            return self._handle_file_operation(
                "move",
                target,
            )

        if intent_name == "rename_file":

            return self._handle_file_operation(
                "rename",
                target,
            )

        # ====================================================
        # REMINDER / ALARM / TIMER
        #
        # These are routed explicitly so the engine does not
        # falsely report success when a scheduler tool is not
        # installed yet.
        # ====================================================

        if intent_name in {
            "reminder",
            "alarm",
            "timer",
            "schedule_task",
        }:

            return (
                f"I understood that you want to set a "
                f"{intent_name.replace('_', ' ')}, but the "
                "scheduler service is not available yet."
            )

        # ----------------------------------------------------
        # UNKNOWN INTENT
        # ----------------------------------------------------

        return (
            "Sorry, I don't have permission "
            "to access or perform that task."
        )

    # ========================================================
    # TIME / DATE HELPERS
    # ========================================================

    @staticmethod
    def _get_current_time() -> str:
        """Return the current local system time."""

        now = datetime.now()

        return (
            f"It's {now.strftime('%I:%M %p').lstrip('0')}."
        )

    @staticmethod
    def _get_current_date() -> str:
        """Return the current local system date."""

        now = datetime.now()

        return (
            f"Today is {now.strftime('%A, %B %d, %Y')}."
        )

    # ========================================================
    # APPLICATION NORMALIZATION
    # ========================================================

    def _normalize_application(
        self,
        target,
    ):
        """Normalize AI/router application names."""

        if not target:
            return target

        aliases = getattr(
            self.router,
            "APPLICATION_ALIASES",
            {},
        )

        return aliases.get(
            target.lower(),
            target,
        )

    # ========================================================
    # MULTI-STEP EXECUTION
    # ========================================================

    def _execute_plan(
        self,
        steps,
    ) -> str:
        """Execute task steps in order."""

        if not steps:

            return (
                "No execution steps were generated."
            )

        results = []

        for index, step in enumerate(
            steps,
            start=1,
        ):

            if not step.action:
                continue

            result = self._execute_intent(
                step.action,
                step.target or "",
            )

            results.append(
                f"Step {index}: {result}"
            )

            # ------------------------------------------------
            # Stop if confirmation is required.
            # ------------------------------------------------

            if self.pending_action is not None:
                break

            # ------------------------------------------------
            # Stop if ACCESS exits.
            # ------------------------------------------------

            if not self.running:
                break

        if not results:

            return (
                "The task plan contained "
                "no executable steps."
            )

        if (
            self.pending_action is not None
        ):

            return (
                "Multi-step task paused:\n"
                + "\n".join(results)
                + "\n\nWaiting for confirmation."
            )

        return (
            "Multi-step task completed:\n"
            + "\n".join(results)
        )

    # ========================================================
    # CONFIRMATION
    # ========================================================

    def _request_confirmation(
        self,
        action: str,
    ) -> str:
        """Request confirmation for dangerous actions."""

        if action not in self.confirmation_actions:

            return (
                "This action is not configured "
                "for confirmation."
            )

        self.pending_action = action

        if action == "shutdown":

            return (
                "Shutdown requested.\n"
                "ACCESS will NOT shut down the "
                "computer yet.\n"
                "Please save your work first.\n"
                "Type 'yes', 'sure', or 'ok' "
                "to confirm.\n"
                "Type 'cancel' to abort."
            )

        if action == "restart":

            return (
                "Restart requested.\n"
                "ACCESS will NOT restart the "
                "computer yet.\n"
                "Please save your work first.\n"
                "Type 'yes', 'sure', or 'ok' "
                "to confirm.\n"
                "Type 'cancel' to abort."
            )

        if action == "sleep":

            return (
                "Sleep requested.\n"
                "ACCESS will NOT put the "
                "computer to sleep yet.\n"
                "Type 'yes', 'sure', or 'ok' "
                "to confirm.\n"
                "Type 'cancel' to abort."
            )

        self.pending_action = None

        return "This action requires confirmation."

    # ========================================================
    # HANDLE CONFIRMATION
    # ========================================================

    def _handle_confirmation(
        self,
        command: str,
    ) -> str:
        """Handle confirmation or cancellation."""

        answer = command.strip().lower()

        # ----------------------------------------------------
        # CANCEL
        # ----------------------------------------------------

        if answer in {
            "cancel",
            "no",
            "n",
            "abort",
            "stop",
        }:

            action = self.pending_action

            self.pending_action = None

            return (
                f"{action.capitalize()} cancelled. "
                "No system action was performed."
            )

        # ----------------------------------------------------
        # CONFIRM
        # ----------------------------------------------------

        if answer in {
            "yes",
            "y",
            "sure",
            "ok",
            "okay",
            "confirm",
            "confirmed",
        }:

            action = self.pending_action

            self.pending_action = None

            return self._execute_confirmed_action(
                action
            )

        return (
            "Confirmation required.\n"
            "Type 'yes', 'sure', or 'ok' "
            "to continue.\n"
            "Type 'cancel' to abort."
        )

    # ========================================================
    # CONFIRMED ACTION
    # ========================================================

    def _execute_confirmed_action(
        self,
        action: str,
    ) -> str:
        """Execute confirmed system actions."""

        if action == "shutdown":

            return self.system.execute_shutdown()

        if action == "restart":

            return self.system.execute_restart()

        if action == "sleep":

            return self.system.execute_sleep()

        return (
            f"Unknown confirmed action: {action}"
        )

    # ========================================================
    # SCREENSHOT
    # ========================================================

    def _handle_screenshot(self) -> str:
        """
        Capture screenshot and open its containing folder.

        macOS:
            ~/Pictures/ACCESS
            Finder opens automatically.

        Windows:
            ~/Pictures/ACCESS
            Explorer opens automatically.

        Linux:
            ~/Pictures/ACCESS
            File manager is opened when possible.
        """

        try:

            screenshot_dir = (
                Path.home()
                / "Pictures"
                / "ACCESS"
            )

            screenshot_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            filename = screenshot_dir / (
                "screenshot_"
                f"{datetime.now():%Y%m%d_%H%M%S}.png"
            )

            system_name = platform.system()

            # ------------------------------------------------
            # macOS
            # ------------------------------------------------

            if system_name == "Darwin":

                subprocess.run(
                    [
                        "screencapture",
                        "-x",
                        str(filename),
                    ],
                    check=True,
                )

            # ------------------------------------------------
            # WINDOWS
            # ------------------------------------------------

            elif system_name == "Windows":

                escaped_path = (
                    str(filename)
                    .replace("'", "''")
                )

                powershell_script = (
                    "Add-Type -AssemblyName "
                    "System.Windows.Forms; "
                    "Add-Type -AssemblyName "
                    "System.Drawing; "
                    "$bounds="
                    "[System.Windows.Forms.Screen]::"
                    "PrimaryScreen.Bounds; "
                    "$bmp=New-Object "
                    "System.Drawing.Bitmap("
                    "$bounds.Width,"
                    "$bounds.Height); "
                    "$g=[System.Drawing.Graphics]::"
                    "FromImage($bmp); "
                    "$g.CopyFromScreen("
                    "$bounds.Location,"
                    "[System.Drawing.Point]::Empty,"
                    "$bounds.Size); "
                    f"$bmp.Save("
                    f"'{escaped_path}',"
                    "[System.Drawing.Imaging.ImageFormat]::Png); "
                    "$g.Dispose(); "
                    "$bmp.Dispose()"
                )

                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        powershell_script,
                    ],
                    check=True,
                )

            # ------------------------------------------------
            # LINUX
            # ------------------------------------------------

            elif system_name == "Linux":

                if shutil.which(
                    "gnome-screenshot"
                ):

                    subprocess.run(
                        [
                            "gnome-screenshot",
                            "-f",
                            str(filename),
                        ],
                        check=True,
                    )

                elif shutil.which("import"):

                    subprocess.run(
                        [
                            "import",
                            "-window",
                            "root",
                            str(filename),
                        ],
                        check=True,
                    )

                elif shutil.which("scrot"):

                    subprocess.run(
                        [
                            "scrot",
                            str(filename),
                        ],
                        check=True,
                    )

                else:

                    return (
                        "Screenshot is unavailable "
                        "on Linux. Install "
                        "gnome-screenshot, "
                        "ImageMagick, or scrot."
                    )

            else:

                return (
                    f"Screenshot is not supported "
                    f"on {system_name}."
                )

            # ------------------------------------------------
            # Verify screenshot exists.
            # ------------------------------------------------

            if not filename.exists():

                return (
                    "Screenshot command completed, "
                    "but the screenshot file could "
                    "not be found."
                )

            # ------------------------------------------------
            # Open containing folder.
            # ------------------------------------------------

            self._open_folder(
                screenshot_dir
            )

            return (
                f"Screenshot saved to: {filename}\n"
                f"Opened folder: {screenshot_dir}"
            )

        except Exception as error:

            return (
                f"Screenshot tool unavailable: "
                f"{error}"
            )

    # ========================================================
    # OPEN FOLDER
    # ========================================================

    @staticmethod
    def _open_folder(
        folder: Path,
    ) -> bool:
        """
        Open a folder in the native file manager.

        Returns True when an open command was launched.
        """

        try:

            system_name = platform.system()

            if system_name == "Darwin":

                subprocess.Popen(
                    [
                        "open",
                        str(folder),
                    ]
                )

                return True

            if system_name == "Windows":

                os.startfile(
                    str(folder)
                )

                return True

            if system_name == "Linux":

                opener = (
                    shutil.which("xdg-open")
                    or shutil.which("gio")
                )

                if opener:

                    subprocess.Popen(
                        [
                            opener,
                            str(folder),
                        ]
                    )

                    return True

        except Exception:

            pass

        return False

    # ========================================================
    # FILE OPERATIONS
    # ========================================================

    def _handle_file_operation(
        self,
        operation: str,
        target: str,
    ) -> str:

        try:

            # ------------------------------------------------
            # CREATE
            # ------------------------------------------------

            if operation == "create":

                path = Path(
                    os.path.expanduser(target)
                )

                if path.exists():

                    return (
                        f"File already exists: "
                        f"{path}"
                    )

                path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                path.touch()

                return (
                    f"File created: {path}"
                )

            # ------------------------------------------------
            # READ
            # ------------------------------------------------

            if operation == "read":

                path = Path(
                    os.path.expanduser(target)
                )

                if not path.exists():

                    return (
                        f"File not found: {path}"
                    )

                if not path.is_file():

                    return (
                        f"Not a file: {path}"
                    )

                content = path.read_text(
                    encoding="utf-8"
                )

                return (
                    content
                    if content
                    else "(File is empty.)"
                )

            # ------------------------------------------------
            # DELETE
            # ------------------------------------------------

            if operation == "delete":

                path = Path(
                    os.path.expanduser(target)
                )

                if not path.exists():

                    return (
                        f"File not found: {path}"
                    )

                if path.is_dir():

                    return (
                        "Delete operation only "
                        f"supports files: {path}"
                    )

                path.unlink()

                return (
                    f"File deleted: {path}"
                )

            # ------------------------------------------------
            # SEARCH
            # ------------------------------------------------

            if operation == "search":

                return self._search_file(
                    target
                )

            # ------------------------------------------------
            # COPY
            # ------------------------------------------------

            if operation == "copy":

                source, destination = (
                    self._split_pair(target)
                )

                source = Path(
                    os.path.expanduser(source)
                )

                destination = Path(
                    os.path.expanduser(
                        destination
                    )
                )

                if not source.exists():

                    return (
                        f"Source not found: "
                        f"{source}"
                    )

                if source.is_dir():

                    shutil.copytree(
                        source,
                        destination,
                        dirs_exist_ok=True,
                    )

                else:

                    if (
                        destination.exists()
                        and destination.is_dir()
                    ):

                        destination = (
                            destination
                            / source.name
                        )

                    destination.parent.mkdir(
                        parents=True,
                        exist_ok=True,
                    )

                    shutil.copy2(
                        source,
                        destination,
                    )

                return (
                    f"Copied: {source} -> "
                    f"{destination}"
                )

            # ------------------------------------------------
            # MOVE
            # ------------------------------------------------

            if operation == "move":

                source, destination = (
                    self._split_pair(target)
                )

                source = Path(
                    os.path.expanduser(source)
                )

                destination = Path(
                    os.path.expanduser(
                        destination
                    )
                )

                if not source.exists():

                    return (
                        f"Source not found: "
                        f"{source}"
                    )

                if (
                    destination.exists()
                    and destination.is_dir()
                ):

                    destination = (
                        destination
                        / source.name
                    )

                destination.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                shutil.move(
                    str(source),
                    str(destination),
                )

                return (
                    f"Moved: {source} -> "
                    f"{destination}"
                )

            # ------------------------------------------------
            # RENAME
            # ------------------------------------------------

            if operation == "rename":

                source, new_name = (
                    self._split_pair(target)
                )

                source = Path(
                    os.path.expanduser(source)
                )

                if not source.exists():

                    return (
                        f"Source not found: "
                        f"{source}"
                    )

                new_name = new_name.strip()

                if not new_name:

                    return (
                        "New name cannot be empty."
                    )

                destination = (
                    source.parent / new_name
                )

                source.rename(
                    destination
                )

                return (
                    f"Renamed: {source} -> "
                    f"{destination}"
                )

            return (
                f"Unsupported file operation: "
                f"{operation}"
            )

        except UnicodeDecodeError:

            return (
                "Unable to read the file "
                "as UTF-8 text."
            )

        except Exception as error:

            return (
                f"File operation failed: "
                f"{error}"
            )

    # ========================================================
    # FILE HELPERS
    # ========================================================

    @staticmethod
    def _split_pair(target: str):

        if "|" not in target:

            raise ValueError(
                "Expected the format "
                "'source|destination'."
            )

        source, destination = (
            target.split("|", 1)
        )

        if (
            not source.strip()
            or not destination.strip()
        ):

            raise ValueError(
                "Source and destination must "
                "both be specified."
            )

        return (
            source.strip(),
            destination.strip(),
        )

    @staticmethod
    def _search_file(
        target: str,
    ) -> str:
        """Search current directory recursively."""

        query = target.strip()

        if not query:

            return (
                "Please specify a filename "
                "to search for."
            )

        root = Path.cwd()

        matches = []

        try:

            for path in root.rglob("*"):

                if (
                    path.is_file()
                    and query.lower()
                    in path.name.lower()
                ):

                    matches.append(path)

                if len(matches) >= 50:
                    break

        except PermissionError:
            pass

        if not matches:

            return (
                f"No files found matching: "
                f"{query}"
            )

        return (
            "Files found:\n"
            + "\n".join(
                str(path)
                for path in matches
            )
        )

    # ========================================================
    # MEMORY
    # ========================================================

    def _save_memory(
        self,
        user_input: str,
        response: str,
    ):
        """Save processed interaction."""

        try:

            self.memory.save(
                user_input,
                response,
            )

        except Exception:

            # Memory failure must never crash ACCESS.

            pass

    # ========================================================
    # RECENT MEMORY
    # ========================================================

    def get_recent_memory(
        self,
        limit=10,
    ):
        """Return recent memory."""

        try:

            return self.memory.recent(
                limit
            )

        except Exception:

            return []

    # ========================================================
    # SEARCH MEMORY
    # ========================================================

    def search_memory(
        self,
        query: str,
        limit=10,
    ):
        """Search stored memory."""

        try:

            return self.memory.search(
                query,
                limit,
            )

        except Exception:

            return []