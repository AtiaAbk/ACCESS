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


class AccessEngine:
    """
    Central execution engine for ACCESS.

    Responsibilities:
    - Receive user commands
    - Interpret commands through AI
    - Use deterministic router
    - Fall back to Local LLM
    - Execute single-step and multi-step tasks
    - Handle dangerous-action confirmation
    - Handle screenshots
    - Handle file operations
    - Store interactions in local memory
    """

    def __init__(self):
        # -------------------------------------------------
        # CORE COMPONENTS
        # -------------------------------------------------

        self.router = IntentRouter()
        self.ai = AIDecisionEngine()
        self.local_llm = LocalLLM()
        self.system = SystemControl()
        self.memory = MemoryDatabase()

        # Compatibility alias
        self.system_tools = self.system

        # -------------------------------------------------
        # ENGINE STATE
        # -------------------------------------------------

        self.running = True
        self.pending_action = None

        # -------------------------------------------------
        # CONFIRMATION ACTIONS
        # -------------------------------------------------

        self.confirmation_actions = {
            "shutdown",
            "restart",
            "sleep",
        }

    # =====================================================
    # MAIN PROCESSOR
    # =====================================================

    def process(self, user_input: str) -> str:
        """
        Process a user command.

        Flow:

            User Input
                 ↓
            Confirmation
                 ↓
            AI Decision Engine
                 ↓
            Deterministic Router
                 ↓
            Local LLM fallback
                 ↓
            Intent Execution
                 ↓
            Memory
        """

        command = (user_input or "").strip()

        if not command:
            response = "Please enter a command."
            self._save_memory(command, response)
            return response

        # -------------------------------------------------
        # PENDING CONFIRMATION
        # -------------------------------------------------

        if self.pending_action is not None:
            response = self._handle_confirmation(command)
            self._save_memory(command, response)
            return response

        # -------------------------------------------------
        # AI DECISION ENGINE
        # -------------------------------------------------

        recent_memory = self.get_recent_memory(5)

        try:
            ai_result = self.ai.interpret(
                command,
                recent_memory=recent_memory,
            )
        except Exception:
            # AI failure must never crash ACCESS.
            ai_result = None

        # -------------------------------------------------
        # AI RESULT
        # -------------------------------------------------

        if ai_result is not None:

            # ---------------------------------------------
            # MULTI-STEP PLAN
            # ---------------------------------------------

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

            # ---------------------------------------------
            # SINGLE AI INTENT
            # ---------------------------------------------

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

        # =================================================
        # DETERMINISTIC ROUTER
        # =================================================

        intent = self.router.route(command)

        # -------------------------------------------------
        # Router successfully recognized command
        # -------------------------------------------------

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

        # =================================================
        # LOCAL LLM FALLBACK
        # =================================================

        if self.local_llm.is_available():

            try:
                local_result = self.local_llm.interpret(
                    command
                )

                if not isinstance(local_result, dict):
                    local_result = {}

                local_intent = local_result.get(
                    "intent",
                    "unknown",
                )

                local_target = local_result.get(
                    "target",
                    "",
                )

                local_response = local_result.get(
                    "response",
                    "",
                )

                # -----------------------------------------
                # NORMAL CONVERSATION
                # -----------------------------------------

                if local_intent == "conversation":
                    response = (
                        local_response
                        or "I'm here to help."
                    )

                    self._save_memory(
                        command,
                        response,
                    )

                    return response

                # -----------------------------------------
                # LOCAL LLM SYSTEM INTENT
                # -----------------------------------------

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

            except Exception:
                # Local LLM failure must never crash ACCESS.
                pass

        # =================================================
        # FINAL UNKNOWN
        # =================================================

        response = self._execute_intent(
            intent.name,
            intent.target,
        )

        self._save_memory(
            command,
            response,
        )

        return response

    # =====================================================
    # INTENT EXECUTION
    # =====================================================

    def _execute_intent(
        self,
        intent_name: str,
        target: str = "",
    ) -> str:
        """
        Execute one structured intent.
        """

        intent_name = (
            intent_name or ""
        ).strip().lower()

        target = target or ""

        # -------------------------------------------------
        # EMPTY
        # -------------------------------------------------

        if intent_name == "empty":
            return "Please enter a command."

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        if intent_name == "unknown":
            if target:
                return (
                    f"I don't know how to handle: "
                    f"{target}"
                )

            return (
                "I don't know how to handle "
                "that command."
            )

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------

        if intent_name == "exit":
            self.running = False
            return "Session terminated safely."

        # -------------------------------------------------
        # DANGEROUS ACTIONS
        # -------------------------------------------------

        if intent_name in self.confirmation_actions:
            return self._request_confirmation(
                intent_name
            )

        # -------------------------------------------------
        # SYSTEM CONTROL
        # -------------------------------------------------

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

        # -------------------------------------------------
        # APPLICATION CONTROL
        # -------------------------------------------------

        if intent_name == "open_application":
            return self.system.open_application(
                self._normalize_application(target)
            )

        if intent_name == "close_application":
            return self.system.close_application(
                self._normalize_application(target)
            )

        # -------------------------------------------------
        # SCREENSHOT
        # -------------------------------------------------

        if intent_name == "screenshot":
            return self._handle_screenshot()

        # -------------------------------------------------
        # FILE OPERATIONS
        # -------------------------------------------------

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

        return (
            f"I don't know how to handle: "
            f"{intent_name}"
        )

    # =====================================================
    # APPLICATION NORMALIZATION
    # =====================================================

    def _normalize_application(self, target):
        """
        Keep AI-generated application names compatible
        with existing router aliases.
        """

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

    # =====================================================
    # MULTI-STEP EXECUTION
    # =====================================================

    def _execute_plan(self, steps) -> str:
        """
        Execute TaskStep objects in order.
        """

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

            # Never continue after confirmation request.
            if self.pending_action is not None:
                break

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

    # =====================================================
    # CONFIRMATION
    # =====================================================

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
                "Please save your work first.\n"
                "Type 'yes', 'sure', or 'ok' "
                "to confirm.\n"
                "Type 'cancel' to abort."
            )

        self.pending_action = None

        return "This action requires confirmation."

    def _handle_confirmation(
        self,
        command: str,
    ) -> str:
        """Handle confirmation or cancellation."""

        answer = command.strip().lower()

        # -------------------------------------------------
        # CANCEL
        # -------------------------------------------------

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

        # -------------------------------------------------
        # CONFIRM
        # -------------------------------------------------

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

    def _execute_confirmed_action(
        self,
        action: str,
    ) -> str:
        """
        Execute confirmed actions through SystemControl.

        No arbitrary shell commands are accepted here.
        """

        if action == "shutdown":
            return self.system.execute_shutdown()

        if action == "restart":
            return self.system.execute_restart()

        if action == "sleep":
            return self.system.execute_sleep()

        return (
            f"Unknown confirmed action: {action}"
        )

    # =====================================================
    # SCREENSHOT
    # =====================================================

    def _handle_screenshot(self) -> str:
        """
        Capture a screenshot using platform-native tools.
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

            # -------------------------------------------------
            # macOS
            # -------------------------------------------------

            if system_name == "Darwin":
                subprocess.run(
                    [
                        "screencapture",
                        "-x",
                        str(filename),
                    ],
                    check=True,
                )

            # -------------------------------------------------
            # Windows
            # -------------------------------------------------

            elif system_name == "Windows":

                escaped_path = str(filename).replace(
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
                    "$bounds.Width,$bounds.Height); "
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

            # -------------------------------------------------
            # Linux
            # -------------------------------------------------

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
                    try:
                        import pyautogui

                        pyautogui.screenshot().save(filename)
                    except Exception:
                        return (
                            "Screenshot is unavailable on this Linux desktop. "
                            "Install grim (Wayland), gnome-screenshot, "
                            "ImageMagick, or scrot."
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

    # =====================================================
    # FILE OPERATIONS
    # =====================================================

    def _handle_file_operation(
        self,
        operation: str,
        target: str,
    ) -> str:
        """Handle local file operations."""

        try:

            # -------------------------------------------------
            # CREATE
            # -------------------------------------------------

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

                return f"File created: {path}"

            # -------------------------------------------------
            # READ
            # -------------------------------------------------

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

            # -------------------------------------------------
            # DELETE
            # -------------------------------------------------

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

                return f"File deleted: {path}"

            # -------------------------------------------------
            # SEARCH
            # -------------------------------------------------

            if operation == "search":
                return self._search_file(target)

            # -------------------------------------------------
            # COPY
            # -------------------------------------------------

            if operation == "copy":

                source, destination = (
                    self._split_pair(target)
                )

                source = Path(
                    os.path.expanduser(source)
                )

                destination = Path(
                    os.path.expanduser(destination)
                )

                if not source.exists():
                    return (
                        f"Source not found: {source}"
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

            # -------------------------------------------------
            # MOVE
            # -------------------------------------------------

            if operation == "move":

                source, destination = (
                    self._split_pair(target)
                )

                source = Path(
                    os.path.expanduser(source)
                )

                destination = Path(
                    os.path.expanduser(destination)
                )

                if not source.exists():
                    return (
                        f"Source not found: {source}"
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

            # -------------------------------------------------
            # RENAME
            # -------------------------------------------------

            if operation == "rename":

                source, new_name = (
                    self._split_pair(target)
                )

                source = Path(
                    os.path.expanduser(source)
                )

                if not source.exists():
                    return (
                        f"Source not found: {source}"
                    )

                new_name = new_name.strip()

                if not new_name:
                    return (
                        "New name cannot be empty."
                    )

                destination = (
                    source.parent / new_name
                )

                source.rename(destination)

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
                f"File operation failed: {error}"
            )

    # =====================================================
    # FILE HELPERS
    # =====================================================

    @staticmethod
    def _split_pair(target: str):
        """
        Split:

            source|destination
        """

        if "|" not in target:
            raise ValueError(
                "Expected the format "
                "'source|destination'."
            )

        source, destination = target.split(
            "|",
            1,
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
        """Search the current directory recursively."""

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
                f"No files found matching: {query}"
            )

        return (
            "Files found:\n"
            + "\n".join(
                str(path)
                for path in matches
            )
        )

    # =====================================================
    # MEMORY
    # =====================================================

    def _save_memory(
        self,
        user_input: str,
        response: str,
    ):
        """Save every processed interaction."""

        try:
            self.memory.save(
                user_input,
                response,
            )
        except Exception:
            # Memory failure must not crash ACCESS.
            pass

    def get_recent_memory(
        self,
        limit=10,
    ):
        """Existing memory API."""

        try:
            return self.memory.recent(limit)
        except Exception:
            return []

    def search_memory(
        self,
        query: str,
        limit=10,
    ):
        """Existing memory API."""

        try:
            return self.memory.search(
                query,
                limit,
            )
        except Exception:
            return []
