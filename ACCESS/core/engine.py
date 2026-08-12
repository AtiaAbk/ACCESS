import os
import platform
import shutil
import subprocess
from pathlib import Path

from core.router import IntentRouter
from tools.system_tools import SystemControl
from memory.database import MemoryDatabase


class AccessEngine:
    """Central engine for ACCESS command processing."""

    def __init__(self):
        self.router = IntentRouter()
        self.system = SystemControl()

        # Local SQLite memory
        self.memory = MemoryDatabase()

        self.running = True

        # Pending dangerous/destructive action.
        self.pending_action = None

        # Actions that require explicit confirmation.
        self.confirmation_actions = {
            "shutdown",
            "restart",
            "sleep",
        }

    # =====================================================
    # MAIN PROCESSOR
    # =====================================================

    def process(self, user_input: str) -> str:
        """Process a user command and store the interaction in ACCESS memory."""

        response = self._process_command(user_input)

        # Memory should never crash ACCESS.
        try:
            command = user_input.strip()
            if command:
                self.memory.save(command, response)
        except Exception:
            pass

        return response

    def _process_command(self, user_input: str) -> str:
        """Process a command without memory handling."""

        command = user_input.strip()

        if not command:
            return "Please enter a command."

        if self.pending_action is not None:
            return self._handle_confirmation(command)

        intent = self.router.route(command)

        if intent.name == "empty":
            return "Please enter a command."

        if intent.name == "exit":
            self.running = False
            return "Session terminated safely."

        # SYSTEM CONTROL
        if intent.name == "shutdown":
            return self._request_confirmation("shutdown")

        if intent.name == "restart":
            return self._request_confirmation("restart")

        if intent.name == "sleep":
            return self._request_confirmation("sleep")

        if intent.name == "lock_screen":
            return self.system.lock_screen()

        if intent.name == "volume_up":
            return self.system.volume_up()

        if intent.name == "volume_down":
            return self.system.volume_down()

        if intent.name == "mute":
            return self.system.mute()

        if intent.name == "brightness_up":
            return self.system.brightness_up()

        if intent.name == "brightness_down":
            return self.system.brightness_down()

        # APPLICATION CONTROL
        if intent.name == "open_application":
            return self.system.open_application(intent.target)

        if intent.name == "close_application":
            return self.system.close_application(intent.target)

        # SCREENSHOT
        if intent.name == "screenshot":
            return self._handle_screenshot()

        # FILE OPERATIONS
        if intent.name == "create_file":
            return self._handle_file_operation("create", intent.target)

        if intent.name == "read_file":
            return self._handle_file_operation("read", intent.target)

        if intent.name == "delete_file":
            return self._handle_file_operation("delete", intent.target)

        if intent.name == "search_file":
            return self._handle_file_operation("search", intent.target)

        if intent.name == "copy_file":
            return self._handle_file_operation("copy", intent.target)

        if intent.name == "move_file":
            return self._handle_file_operation("move", intent.target)

        if intent.name == "rename_file":
            return self._handle_file_operation("rename", intent.target)

        return f"I don't know how to handle: {command}"

    # =====================================================
    # MEMORY
    # =====================================================

    def get_recent_memory(self, limit=10):
        """Return recent ACCESS memories."""
        try:
            return self.memory.recent(limit)
        except Exception:
            return []

    def search_memory(self, query: str, limit=10):
        """Search stored ACCESS memories."""
        try:
            return self.memory.search(query, limit)
        except Exception:
            return []

    # =====================================================
    # CONFIRMATION
    # =====================================================

    def _request_confirmation(self, action: str) -> str:
        """Put a destructive system action into a pending confirmation state."""

        if action not in self.confirmation_actions:
            return "This action is not configured for confirmation."

        self.pending_action = action

        if action == "shutdown":
            return (
                "Shutdown requested.\n"
                "ACCESS will NOT shut down the computer yet.\n"
                "Please save your work first.\n"
                "Type 'yes', 'sure', or 'ok' to confirm.\n"
                "Type 'cancel' to abort."
            )

        if action == "restart":
            return (
                "Restart requested.\n"
                "ACCESS will NOT restart the computer yet.\n"
                "Please save your work first.\n"
                "Type 'yes', 'sure', or 'ok' to confirm.\n"
                "Type 'cancel' to abort."
            )

        if action == "sleep":
            return (
                "Sleep requested.\n"
                "ACCESS will NOT put the computer to sleep yet.\n"
                "Type 'yes', 'sure', or 'ok' to confirm.\n"
                "Type 'cancel' to abort."
            )

        self.pending_action = None
        return "This action requires confirmation."

    def _handle_confirmation(self, command: str) -> str:
        """Handle confirmation or cancellation."""

        answer = command.strip().lower()

        if answer in {"cancel", "no", "n", "abort", "stop"}:
            action = self.pending_action
            self.pending_action = None
            return (
                f"{action.capitalize()} cancelled. "
                "No system action was performed."
            )

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
            return self._execute_confirmed_action(action)

        return (
            "Confirmation required.\n"
            "Type 'yes', 'sure', or 'ok' to continue.\n"
            "Type 'cancel' to abort."
        )

    def _execute_confirmed_action(self, action: str) -> str:
        """Execute an already-confirmed system action."""

        if action == "shutdown":
            return self.system.execute_shutdown()

        if action == "restart":
            return self.system.execute_restart()

        if action == "sleep":
            return self.system.execute_sleep()

        return f"Unknown confirmed action: {action}"

    # =====================================================
    # SCREENSHOT
    # =====================================================

    def _handle_screenshot(self) -> str:
        """Capture a screenshot without requiring another module."""

        try:
            screenshot_dir = Path.home() / "Pictures" / "ACCESS"
            screenshot_dir.mkdir(parents=True, exist_ok=True)

            filename = screenshot_dir / (
                f"screenshot_{__import__('datetime').datetime.now():%Y%m%d_%H%M%S}.png"
            )

            if platform.system() == "Darwin":
                subprocess.run(
                    ["screencapture", "-x", str(filename)],
                    check=True,
                )

            elif platform.system() == "Windows":
                powershell_script = (
                    "Add-Type -AssemblyName System.Windows.Forms; "
                    "Add-Type -AssemblyName System.Drawing; "
                    "$bounds=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
                    f"$bmp=New-Object System.Drawing.Bitmap($bounds.Width,$bounds.Height); "
                    "$g=[System.Drawing.Graphics]::FromImage($bmp); "
                    "$g.CopyFromScreen($bounds.Location,[System.Drawing.Point]::Empty,$bounds.Size); "
                    f"$bmp.Save('{str(filename).replace(chr(39), chr(39)+chr(39))}',"
                    "[System.Drawing.Imaging.ImageFormat]::Png); "
                    "$g.Dispose(); $bmp.Dispose()"
                )
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", powershell_script],
                    check=True,
                )

            elif platform.system() == "Linux":
                if shutil.which("gnome-screenshot"):
                    subprocess.run(
                        ["gnome-screenshot", "-f", str(filename)],
                        check=True,
                    )
                elif shutil.which("import"):
                    subprocess.run(
                        ["import", "-window", "root", str(filename)],
                        check=True,
                    )
                elif shutil.which("scrot"):
                    subprocess.run(
                        ["scrot", str(filename)],
                        check=True,
                    )
                else:
                    return (
                        "Screenshot is unavailable on Linux. "
                        "Install gnome-screenshot, ImageMagick, or scrot."
                    )
            else:
                return f"Screenshot is not supported on {platform.system()}."

            return f"Screenshot saved to: {filename}"

        except Exception as error:
            return f"Screenshot tool unavailable: {error}"

    # =====================================================
    # FILE OPERATIONS
    # =====================================================

    def _handle_file_operation(self, operation: str, target: str) -> str:
        """Handle file operations directly."""

        try:
            if operation == "create":
                path = Path(os.path.expanduser(target))
                if path.exists():
                    return f"File already exists: {path}"

                path.parent.mkdir(parents=True, exist_ok=True)
                path.touch()
                return f"File created: {path}"

            if operation == "read":
                path = Path(os.path.expanduser(target))
                if not path.exists():
                    return f"File not found: {path}"
                if not path.is_file():
                    return f"Not a file: {path}"

                content = path.read_text(encoding="utf-8")
                return content if content else "(File is empty.)"

            if operation == "delete":
                path = Path(os.path.expanduser(target))
                if not path.exists():
                    return f"File not found: {path}"
                if path.is_dir():
                    return f"Delete operation only supports files: {path}"

                path.unlink()
                return f"File deleted: {path}"

            if operation == "search":
                return self._search_file(target)

            if operation == "copy":
                source, destination = self._split_pair(target)
                source = Path(os.path.expanduser(source))
                destination = Path(os.path.expanduser(destination))

                if not source.exists():
                    return f"Source not found: {source}"

                if source.is_dir():
                    shutil.copytree(source, destination, dirs_exist_ok=True)
                else:
                    if destination.exists() and destination.is_dir():
                        destination = destination / source.name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)

                return f"Copied: {source} -> {destination}"

            if operation == "move":
                source, destination = self._split_pair(target)
                source = Path(os.path.expanduser(source))
                destination = Path(os.path.expanduser(destination))

                if not source.exists():
                    return f"Source not found: {source}"

                if destination.exists() and destination.is_dir():
                    destination = destination / source.name

                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(destination))
                return f"Moved: {source} -> {destination}"

            if operation == "rename":
                source, new_name = self._split_pair(target)
                source = Path(os.path.expanduser(source))

                if not source.exists():
                    return f"Source not found: {source}"

                new_name = new_name.strip()
                if not new_name:
                    return "New name cannot be empty."

                destination = source.parent / new_name
                source.rename(destination)
                return f"Renamed: {source} -> {destination}"

            return f"Unsupported file operation: {operation}"

        except UnicodeDecodeError:
            return "Unable to read the file as UTF-8 text."
        except Exception as error:
            return f"File operation failed: {error}"

    @staticmethod
    def _split_pair(target: str):
        """Split a source|destination pair safely."""
        if "|" not in target:
            raise ValueError(
                "Expected the format 'source|destination'."
            )
        source, destination = target.split("|", 1)
        if not source.strip() or not destination.strip():
            raise ValueError(
                "Source and destination must both be specified."
            )
        return source.strip(), destination.strip()

    @staticmethod
    def _search_file(target: str) -> str:
        """Search from the current directory for a filename/path fragment."""

        query = target.strip()
        if not query:
            return "Please specify a filename to search for."

        root = Path.cwd()
        matches = []

        try:
            for path in root.rglob("*"):
                if path.is_file() and query.lower() in path.name.lower():
                    matches.append(path)

                if len(matches) >= 50:
                    break

        except PermissionError:
            pass

        if not matches:
            return f"No files found matching: {query}"

        return "Files found:\n" + "\n".join(str(path) for path in matches)