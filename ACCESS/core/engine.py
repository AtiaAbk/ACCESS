import ast
import operator
import os
import platform
import random
import re
import shutil
import subprocess

from pathlib import Path
from datetime import datetime

from ai.decision_engine import AIDecisionEngine
from ai.local_llm import LocalLLM
from core.router import IntentRouter
from memory.database import MemoryDatabase
from tools.system_tools import SystemControl
from app.reminders import ReminderService
from app.system_monitor import SystemMonitor, format_bytes, format_duration
from plugins.smart_home import SmartHomeHub


# ============================================================
# ACCESS ENGINE
# ============================================================

class AccessEngine:
    """
    Central execution engine for ACCESS.

    Responsibilities:
    - Receive user commands
    - Deterministic command routing
    - AI interpretation & goal detection
    - Compound multi-step task planning
    - Local LLM & cloud AI fallback
    - Zero-dependency offline conversational heuristics
    - Real-time system monitoring & health stats
    - Scheduling & persistent reminders
    - IoT Smart Home & security automation
    - Execute single-step & multi-step tasks
    - Handle confirmation for destructive actions
    - Handle screenshots & file operations
    - Store interactions in local SQLite memory
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self):

        # ----------------------------------------------------
        # CORE COMPONENTS
        # ----------------------------------------------------

        self.router = IntentRouter()

        self.local_llm = LocalLLM()

        self.system = SystemControl()

        self.memory = MemoryDatabase()

        self.ai = AIDecisionEngine(local_llm=self.local_llm)

        # Compatibility alias
        self.system_tools = self.system

        # ----------------------------------------------------
        # APPLICATION & PLUGIN INTEGRATIONS
        # ----------------------------------------------------

        data_dir = Path(__file__).resolve().parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)

        self.reminders = ReminderService(data_dir / "reminders.json")

        self.monitor = SystemMonitor()

        self.smart_home = SmartHomeHub(data_dir / "smart_home.json")

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

    # ========================================================
    # MAIN PROCESSOR
    # ========================================================

    def process(self, user_input: str) -> str:
        """
        Main ACCESS processing pipeline.

        Processing Priority:
        1. Pending confirmation check
        2. Fast date / time / day queries (deterministic, zero latency)
        3. Deterministic command routing (explicit desktop & system tasks)
        4. AI Decision Engine (Goal Detector, Compound Plans, Memory Fallback)
        5. Smart Home & Security device commands
        6. Reminders & Scheduling
        7. Safe math evaluation
        8. Natural Conversation (Local LLM -> Cloud Gemini -> Offline Heuristics)
        """

        command = (user_input or "").strip()

        if not command:
            return "Please enter a message."

        # ----------------------------------------------------
        # 1. PENDING CONFIRMATION
        # ----------------------------------------------------

        if self.pending_action is not None:
            response = self._handle_confirmation(command)
            self._save_memory(command, response)
            return response

        # ----------------------------------------------------
        # 2. DATE / TIME / DAY (Fast, zero dependencies)
        # ----------------------------------------------------

        datetime_response = self._handle_datetime_query(command)
        if datetime_response is not None:
            self._save_memory(command, datetime_response)
            return datetime_response

        # ----------------------------------------------------
        # 3. DETERMINISTIC COMMAND ROUTING
        # ----------------------------------------------------

        intents = self.router.route_all(command)

        executable_intents = [
            intent for intent in intents
            if intent.name not in {"unknown", "empty"}
        ]

        if executable_intents:
            results = []

            for intent in executable_intents:
                result = self._execute_intent(
                    intent.name,
                    intent.target,
                )
                results.append(result)

                if self.pending_action is not None:
                    break

                if not self.running:
                    break

            response = "\n".join(results)
            self._save_memory(command, response)
            return response

        # ----------------------------------------------------
        # 4. AI DECISION ENGINE (Goal Detection, Plans, Memory)
        # ----------------------------------------------------

        recent_memory = self.get_recent_memory(8)
        try:
            ai_result = self.ai.interpret(
                command,
                recent_memory=recent_memory,
            )
        except Exception:
            ai_result = None

        if ai_result is not None:
            # Compound Multi-Step Plan
            if (
                ai_result.intent == "multi_step_plan"
                and ai_result.steps
                and ai_result.confidence >= self.ai.CONFIDENCE_THRESHOLD
            ):
                response = self._execute_plan(ai_result.steps)
                self._save_memory(command, response)
                return response

            # Single executable intent identified by AI goal detector
            if (
                ai_result.intent
                and ai_result.intent not in {"unknown", "conversation"}
                and ai_result.confidence >= self.ai.CONFIDENCE_THRESHOLD
            ):
                response = self._execute_intent(
                    ai_result.intent,
                    ai_result.target or "",
                )
                self._save_memory(command, response)
                return response

        # ----------------------------------------------------
        # 5. SMART HOME & SECURITY
        # ----------------------------------------------------

        smart_home_resp = self.smart_home.handle_command(command)
        if smart_home_resp:
            self._save_memory(command, smart_home_resp)
            return smart_home_resp

        # ----------------------------------------------------
        # 6. REMINDERS & SCHEDULING
        # ----------------------------------------------------

        reminder_resp = self.reminders.interpret(command)
        if reminder_resp:
            self._save_memory(command, reminder_resp)
            return reminder_resp

        # ----------------------------------------------------
        # 7. SAFE MATH CALCULATION
        # ----------------------------------------------------

        math_resp = self._handle_math(command)
        if math_resp is not None:
            self._save_memory(command, math_resp)
            return math_resp

        # ----------------------------------------------------
        # 8. CONVERSATION (Ollama -> Cloud -> Offline Fallback)
        # ----------------------------------------------------

        response = self._chat_with_llm(command)
        self._save_memory(command, response)
        return response

    # ========================================================
    # CONVERSATIONAL AGENT (MULTI-TIERED)
    # ========================================================

    def _chat_with_llm(self, user_input: str) -> str:
        """
        Intelligent multi-tier conversation engine:
        Tier 1: Local Ollama (if active)
        Tier 2: Cloud Gemini API (if GEMINI_API_KEY is configured)
        Tier 3: Offline Conversational Heuristics (100% offline fallback)
        """

        # Tier 1: Local Ollama
        if self.local_llm.is_available():
            try:
                recent = self.get_recent_memory(8)

                chat_method = getattr(self.local_llm, "chat", None)
                if callable(chat_method):
                    try:
                        raw = chat_method(user_input, recent_memory=recent)
                    except TypeError:
                        raw = chat_method(user_input)
                    normalized = self._normalize_llm_response(raw)
                    if normalized and not normalized.startswith("I didn't get a response"):
                        return normalized

                interpret_method = getattr(self.local_llm, "interpret", None)
                if callable(interpret_method):
                    result = interpret_method(user_input)
                    if isinstance(result, dict) and result.get("response"):
                        return str(result["response"]).strip()
            except Exception:
                pass

        # Tier 2: Cloud Gemini API (if key is set)
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import requests
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-1.5-flash:generateContent?key={gemini_key}"
                )
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": (
                                "You are ACCESS, a smart desktop assistant. "
                                f"Answer helpfully and concisely: {user_input}"
                            )
                        }]
                    }]
                }
                res = requests.post(url, json=payload, timeout=8)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "").strip()
            except Exception:
                pass

        # Tier 3: Zero-dependency Offline Conversational Engine
        return self._offline_conversational_fallback(user_input)

    @staticmethod
    def _normalize_llm_response(result) -> str:
        """Convert common Ollama/LocalLLM return shapes to plain text."""

        if result is None:
            return "I didn't get a response from the local model."

        if isinstance(result, str):
            text = result.strip()
            return text or "I didn't get a response from the local model."

        if isinstance(result, dict):
            for key in ("response", "text", "content", "message"):
                value = result.get(key)
                if isinstance(value, dict):
                    value = value.get("content") or value.get("text")
                if value:
                    return str(value).strip()

        # Ollama-style response object support.
        response_attr = getattr(result, "response", None)
        if response_attr:
            return str(response_attr).strip()

        message_attr = getattr(result, "message", None)
        if message_attr:
            if isinstance(message_attr, dict):
                return str(
                    message_attr.get("content")
                    or message_attr.get("text")
                    or message_attr
                ).strip()
            content = getattr(message_attr, "content", None)
            if content:
                return str(content).strip()

        return str(result).strip()

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
                "I don't have permission "
                "to do this."
            )

        # ----------------------------------------------------
        # ABOUT
        # ----------------------------------------------------

        if intent_name == "about":
            return (
                "I am ACCESS.\n"
                "Adaptive Cognitive Companion "
                "for Efficient System Services.\n"
                "An Intelligent Desktop Assistant."
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
        # STATUS, HELP, DEMO
        # ====================================================

        if intent_name == "status":
            return self._get_access_status()

        if intent_name in {"help", "commands"}:
            return self._get_help_text()

        if intent_name == "demo":
            return self._run_demo()

        # ====================================================
        # SYSTEM HEALTH & MONITORING
        # ====================================================

        if intent_name == "system_status":
            return self._get_system_health_report()

        if intent_name == "battery_status":
            return self._get_battery_status()

        if intent_name == "cpu_status":
            return self._get_cpu_status()

        if intent_name == "memory_status":
            return self._get_memory_status()

        # ====================================================
        # MULTI-STEP WORKSPACE PLANS
        # ====================================================

        if intent_name == "multi_step_plan":
            steps = self.ai.task_planner.plan(target)
            if steps:
                return self._execute_plan(steps)
            return f"No execution steps defined for workspace '{target}'."

        # ====================================================
        # SCHEDULING & REMINDERS
        # ====================================================

        if intent_name == "set_reminder":
            return self.reminders.interpret(target) or f"Reminder set: {target}"

        if intent_name == "list_reminders":
            return self.reminders.describe()

        if intent_name == "cancel_reminder":
            if self.reminders.cancel(target):
                return f"Reminder {target} was cancelled."
            return f"Could not find reminder with ID '{target}'."

        # ====================================================
        # SMART HOME & SECURITY
        # ====================================================

        if intent_name in {"smart_home", "smart_home_status"}:
            resp = self.smart_home.handle_command(target) if target else None
            return resp or self.smart_home.get_summary()

        if intent_name == "security_status":
            return self.smart_home.get_security_summary()

        if intent_name == "arm_security":
            return self.smart_home.handle_command(f"arm security {target}") or "Security armed."

        if intent_name == "disarm_security":
            return self.smart_home.handle_command("disarm security") or "Security disarmed."

        if intent_name == "emergency_alarm":
            return self.smart_home.handle_command("trigger alarm") or "Alarm triggered!"

        # ====================================================
        # MATH & UTILITY
        # ====================================================

        if intent_name == "calculate":
            math_res = self._handle_math(target)
            return math_res or f"Could not calculate: {target}"

        if intent_name == "clear":
            return "\n" * 30 + "Terminal screen cleared."

        # ----------------------------------------------------
        # UNKNOWN INTENT
        # ----------------------------------------------------

        return (
            "I don't have permission "
            "to do this."
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

            # Stop if confirmation is required.

            if self.pending_action is not None:
                break

            # Stop if ACCESS exits.

            if not self.running:
                break

        if not results:
            return (
                "The task plan contained "
                "no executable steps."
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
        """Capture a screenshot using platform tools."""

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

                escaped_path = str(
                    filename
                ).replace(
                    "'",
                    "''",
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

                elif shutil.which("grim"):
                    subprocess.run(
                        [
                            "grim",
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
                        "gnome-screenshot, ImageMagick, "
                        "or scrot."
                    )

            else:

                return (
                    f"Screenshot is not supported "
                    f"on {system_name}."
                )

            return (
                f"Screenshot saved to: {filename}"
            )

        except Exception as error:

            return (
                f"Screenshot tool unavailable: "
                f"{error}"
            )

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
    def _search_file(target: str) -> str:
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

    # ========================================================
    # DATE / TIME / DAY HANDLER
    # ========================================================

    def _handle_datetime_query(self, command: str) -> str | None:
        """Handle basic date, time and day queries deterministically with zero latency."""
        text = command.strip().lower()
        normalized = (
            text.replace("today's", "todays")
            .replace("what's", "what is")
            .replace("whats", "what is")
        )

        time_phrases = (
            "what time is it", "what is the time", "what is current time",
            "what is the current time", "tell me the time", "tell me current time",
            "tell me the current time", "current time", "time now", "what time",
        )
        date_phrases = (
            "what is today's date", "what is todays date", "what is the date",
            "tell me today's date", "tell me todays date", "tell me the date",
            "current date", "today's date", "todays date", "what date is it",
        )
        day_phrases = (
            "what day is today", "what day is it", "tell me what day it is",
            "tell me the day", "which day is today", "what is the day today",
        )

        now = datetime.now()
        if any(phrase in normalized for phrase in time_phrases):
            return f"It's {now.strftime('%I:%M:%S %p')}."
        if any(phrase in normalized for phrase in date_phrases):
            return f"Today is {now.strftime('%B %d, %Y')}."
        if any(phrase in normalized for phrase in day_phrases):
            return f"Today is {now.strftime('%A')}."
        return None

    # ========================================================
    # SAFE ARITHMETIC / MATH EVALUATOR
    # ========================================================

    @staticmethod
    def _handle_math(text: str) -> str | None:
        """Safely calculate basic arithmetic expressions without eval."""
        cleaned = text.strip().lower()
        for prefix in ("calculate", "solve", "what is", "math"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        cleaned = cleaned.rstrip("?!., ")
        if not cleaned:
            return None

        # Operator translation
        cleaned = cleaned.replace("times", "*").replace("multiplied by", "*")
        cleaned = cleaned.replace("divided by", "/").replace("over", "/")
        cleaned = cleaned.replace("plus", "+").replace("minus", "-")
        cleaned = cleaned.replace("^", "**")

        allowed_chars = set("0123456789+-*/().% ")
        if not all(c in allowed_chars for c in cleaned):
            return None

        if not any(op in cleaned for op in "+-*/%"):
            return None

        try:
            tree = ast.parse(cleaned, mode="eval")
            operators = {
                ast.Add: operator.add,
                ast.Sub: operator.sub,
                ast.Mult: operator.mul,
                ast.Div: operator.truediv,
                ast.FloorDiv: operator.floordiv,
                ast.Mod: operator.mod,
                ast.Pow: operator.pow,
                ast.USub: operator.neg,
                ast.UAdd: operator.pos,
            }

            def _eval_node(node):
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    return node.value
                if isinstance(node, ast.BinOp) and type(node.op) in operators:
                    left = _eval_node(node.left)
                    right = _eval_node(node.right)
                    return operators[type(node.op)](left, right)
                if isinstance(node, ast.UnaryOp) and type(node.op) in operators:
                    operand = _eval_node(node.operand)
                    return operators[type(node.op)](operand)
                raise ValueError("Unsupported node")

            result = _eval_node(tree.body)
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            formatted = f"{result:,}" if isinstance(result, int) else f"{result:.4f}".rstrip("0").rstrip(".")
            return f"{cleaned.replace('**', '^')} = {formatted}"
        except Exception:
            return None

    # ========================================================
    # STATUS & SYSTEM MONITORING REPORTS
    # ========================================================

    def _get_access_status(self) -> str:
        """Format ACCESS core engine status."""
        llm_status = "[green]● ONLINE (Ollama)[/green]" if self.local_llm.is_available() else "[yellow]● STANDBY (Offline Fallback Ready)[/yellow]"
        sec_status = f"[green]● {self.smart_home.security_mode.upper()}[/green]" if self.smart_home.security_mode != "Disarmed" else "[yellow]● DISARMED[/yellow]"
        return (
            "╭──────────────── ACCESS STATUS ────────────────╮\n"
            "│ SYSTEM:        [green]● ONLINE[/green]                       │\n"
            "│ ENGINE:        [green]● READY[/green]                        │\n"
            "│ ROUTER:        [green]● READY[/green]                        │\n"
            "│ AI LAYER:      [green]● ACTIVE[/green] (Goal Detector + Plans) │\n"
            "│ MODE:          [yellow]OFFLINE-FIRST[/yellow]                 │\n"
            f"│ PLATFORM:      {platform.system()} ({platform.machine()})\n"
            f"│ LOCAL LLM:     {llm_status}\n"
            f"│ SMART HOME:    {sec_status}\n"
            "│ VERSION:       1.0 (Tech Fair Release)         │\n"
            "╰───────────────────────────────────────────────╯"
        )

    def _get_system_health_report(self) -> str:
        """Format real-time CPU, RAM, Disk, Battery, and Network metrics."""
        snap = self.monitor.snapshot()
        battery_str = "N/A"
        if snap.battery_percent is not None:
            plugged = " (Plugged In)" if snap.battery_plugged else " (On Battery)"
            battery_str = f"{snap.battery_percent:.0f}%{plugged}"
        return (
            "🖥️ [bold cyan]System Health & Performance Monitor[/bold cyan]\n"
            "──────────────────────────────────────────────\n"
            f"• Device:    {snap.device_name} ({snap.os_version})\n"
            f"• CPU Load:  {snap.cpu_percent:.1f}%\n"
            f"• Memory:    {snap.memory_percent:.1f}% ({format_bytes(snap.memory_used)} used / {format_bytes(snap.memory_total)} total)\n"
            f"• Disk:      {snap.disk_percent:.1f}% ({format_bytes(snap.disk_used)} used / {format_bytes(snap.disk_total)} total)\n"
            f"• Battery:   {battery_str}\n"
            f"• Network:   ↓ {format_bytes(snap.network_download_rate)}/s | ↑ {format_bytes(snap.network_upload_rate)}/s\n"
            f"• Uptime:    {format_duration(snap.uptime_seconds)}"
        )

    def _get_battery_status(self) -> str:
        snap = self.monitor.snapshot()
        if snap.battery_percent is None:
            return "Battery information is not available on this device (Desktop power source)."
        state = "Charging / Plugged in" if snap.battery_plugged else "Discharging"
        return f"🔋 Battery Level: {snap.battery_percent:.0f}% ({state})"

    def _get_cpu_status(self) -> str:
        snap = self.monitor.snapshot()
        return f"⚡ CPU Utilization: {snap.cpu_percent:.1f}% across all cores."

    def _get_memory_status(self) -> str:
        snap = self.monitor.snapshot()
        return f"🧠 RAM Utilization: {snap.memory_percent:.1f}% ({format_bytes(snap.memory_used)} used of {format_bytes(snap.memory_total)} total)."

    def _get_help_text(self) -> str:
        """Return the comprehensive ACCESS command reference."""
        return (
            "📋 [bold cyan]ACCESS Command Reference[/bold cyan]\n"
            "────────────────────────────────────────────────────────\n"
            "[bold white]General Commands:[/bold white]\n"
            "  • help / commands            - Show this command reference\n"
            "  • status                     - Show ACCESS engine status\n"
            "  • system health / battery    - Real-time CPU, RAM, Battery & Network\n"
            "  • demo                       - Run Tech Fair interactive live showcase\n"
            "  • about                      - Project details & architecture\n"
            "  • clear                      - Clear the screen\n"
            "  • exit                       - Exit ACCESS\n\n"
            "[bold white]Application & System Control:[/bold white]\n"
            "  • open / close <app>         - e.g. 'open chrome', 'open calculator'\n"
            "  • screenshot                 - Capture full screen\n"
            "  • volume up / down / mute    - Control audio levels\n"
            "  • brightness up / down       - Adjust display brightness\n"
            "  • dark mode / light mode     - Toggle system appearance\n"
            "  • lock screen                - Lock the computer\n"
            "  • shutdown / restart / sleep - Power control (with safety confirmation)\n\n"
            "[bold white]Multi-Step Workspaces:[/bold white]\n"
            "  • prepare development workspace - Launch VS Code + Terminal + Chrome\n"
            "  • prepare writing workspace     - Launch Notes + Chrome\n"
            "  • prepare presentation          - Launch Keynote + Chrome\n\n"
            "[bold white]File Management:[/bold white]\n"
            "  • create file <name>         - Create a file\n"
            "  • read file <path>           - Read file contents\n"
            "  • search file <name>         - Locate files\n"
            "  • copy / move / rename file  - File manipulation\n"
            "  • delete file <path>         - Remove a file\n\n"
            "[bold white]Scheduling & Reminders:[/bold white]\n"
            "  • remind me in <N> minutes to <task>\n"
            "  • remind me at <time> to <task>\n"
            "  • show reminders / cancel reminder <id>\n\n"
            "[bold white]Smart Home & Security Hub:[/bold white]\n"
            "  • smart home / home status   - IoT devices overview\n"
            "  • turn on/off living room light\n"
            "  • set thermostat to 22 degrees\n"
            "  • arm security / disarm security\n"
            "  • lock / unlock front door\n"
            "  • trigger emergency alarm\n\n"
            "[bold white]Natural Conversation & Math:[/bold white]\n"
            "  • 'what time is it', 'what is today's date'\n"
            "  • 'calculate 25 * 40', 'solve 1024 / 8'\n"
            "  • Ask questions or chat naturally!"
        )

    def _run_demo(self) -> str:
        """Run an impressive showcase walkthrough for the tech fair."""
        return (
            "🌟 [bold cyan]ACCESS Live Demonstration Showcase[/bold cyan]\n"
            "──────────────────────────────────────────────────────\n"
            "Welcome to ACCESS — Adaptive Cognitive Companion for Efficient System Services!\n\n"
            "Key Architectural Pillars:\n"
            "1. 🔒 [bold green]100% Privacy & Local-First[/bold green]: All core routines, routers, and tools run on-device.\n"
            "2. ⚡ [bold cyan]Deterministic & Hybrid AI Engine[/bold cyan]: Zero-latency command execution with multi-step reasoning.\n"
            "3. 🖥️ [bold white]Desktop Automation[/bold white]: Native control of apps, volume, brightness, dark mode, files, and screenshots.\n"
            "4. 🏠 [bold magenta]IoT Smart Home Hub[/bold magenta]: Room-based automation, sensor monitoring, and security alarm dispatch.\n\n"
            "Try these commands in your live demo:\n"
            "• 'prepare my development workspace'  → Compound task execution\n"
            "• 'system health'                    → Real-time CPU, RAM, Battery & Network\n"
            "• 'turn on living room light'        → Smart Home IoT control\n"
            "• 'arm security away'                → Intelligent security system arming\n"
            "• 'take a screenshot'                → Screen capture with thumbnail preview\n"
            "• 'remind me in 5 minutes to submit' → Persistent scheduling\n"
            "• 'turn on dark mode'                → System appearance toggle"
        )

    def _offline_conversational_fallback(self, user_input: str) -> str:
        """Zero-dependency offline conversational heuristics."""
        cleaned = user_input.strip().lower()

        # Greetings
        if cleaned in {
            "hi", "hello", "hey", "hola", "greetings",
            "good morning", "good afternoon", "good evening",
            "hi access", "hello access", "hey access",
        }:
            greetings = [
                "Hello! I am ACCESS, your intelligent desktop companion. How can I assist you today?",
                "Greetings! ACCESS is online and ready for your commands.",
                "Hi there! System status is optimal. What would you like to do?",
            ]
            return random.choice(greetings)

        # Identity & Creator
        if any(p in cleaned for p in ["who are you", "what are you", "introduce yourself"]):
            return (
                "I am ACCESS — Adaptive Cognitive Companion for Efficient System Services.\n"
                "I'm an offline-first desktop assistant designed for complete local automation, "
                "privacy, intelligent task execution, and system control."
            )

        if any(p in cleaned for p in ["who made you", "who created you", "who developed you", "who built you"]):
            return (
                "I was developed by Atia Oishi as a cross-platform desktop AI assistant and "
                "smart home operating companion for the tech fair!"
            )

        # How are you
        if any(p in cleaned for p in ["how are you", "how are you doing", "how are you today"]):
            return "Operating at 100% capacity! All modules, security policies, and automation engines are green."

        # Jokes
        if any(p in cleaned for p in ["tell me a joke", "joke", "make me laugh"]):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "Why was the computer cold? It left its Windows open!",
                "A SQL query walks into a bar, walks up to two tables and asks: 'Can I join you?'",
            ]
            return random.choice(jokes)

        # Gratitude
        if any(p in cleaned for p in ["thank you", "thanks", "appreciate it"]):
            return "You're very welcome! Always here to make your system run smoother."

        # General helpful guidance
        return (
            f"I heard: '{user_input}'\n"
            "I am currently operating in local-first mode. Here are some things you can try:\n"
            "• 'help' — View all available commands\n"
            "• 'status' — View ACCESS core engine status\n"
            "• 'system health' — Inspect CPU, RAM, Disk, and Battery\n"
            "• 'demo' — Run the live Tech Fair presentation showcase\n"
            "• 'smart home' — Check virtual IoT devices and security\n"
            "• 'prepare my development workspace' — Launch developer tools\n"
            "• 'take a screenshot' — Capture the screen\n"
            "• 'what time is it' or 'calculate 25 * 4' — Ask for time, date, or math"
        )
