"""
ACCESS Core Engine

Central execution engine for ACCESS.
Handles intent routing, system tools, file tools,
and confirmation for destructive system actions.
"""

from core.router import IntentRouter
from tools.system_tools import SystemControl


class AccessEngine:
    """Central engine for ACCESS command processing."""

    def __init__(self):
        self.router = IntentRouter()
        self.system = SystemControl()

        self.running = True

        # Pending dangerous/destructive action.
        # Example: "shutdown"
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
        """Process a user command and return a response."""

        command = user_input.strip()

        if not command:
            return "Please enter a command."

        # -------------------------------------------------
        # Handle pending confirmation first
        # -------------------------------------------------

        if self.pending_action is not None:
            return self._handle_confirmation(command)

        # -------------------------------------------------
        # Route normal command
        # -------------------------------------------------

        intent = self.router.route(command)

        # -------------------------------------------------
        # EXIT
        # -------------------------------------------------

        if intent.name == "exit":
            self.running = False
            return "Session terminated safely."

        # -------------------------------------------------
        # SYSTEM CONTROL
        # -------------------------------------------------

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

        # -------------------------------------------------
        # APPLICATION CONTROL
        # -------------------------------------------------

        if intent.name == "open_application":
            return self.system.open_application(
                intent.target
            )

        if intent.name == "close_application":
            return self.system.close_application(
                intent.target
            )

        # -------------------------------------------------
        # SCREENSHOT
        # -------------------------------------------------

        if intent.name == "screenshot":
            return self._handle_screenshot()

        # -------------------------------------------------
        # FILE OPERATIONS
        # -------------------------------------------------

        if intent.name == "create_file":
            return self._handle_file_operation(
                "create",
                intent.target,
            )

        if intent.name == "read_file":
            return self._handle_file_operation(
                "read",
                intent.target,
            )

        if intent.name == "delete_file":
            return self._handle_file_operation(
                "delete",
                intent.target,
            )

        if intent.name == "search_file":
            return self._handle_file_operation(
                "search",
                intent.target,
            )

        if intent.name == "copy_file":
            return self._handle_file_operation(
                "copy",
                intent.target,
            )

        if intent.name == "move_file":
            return self._handle_file_operation(
                "move",
                intent.target,
            )

        if intent.name == "rename_file":
            return self._handle_file_operation(
                "rename",
                intent.target,
            )

        # -------------------------------------------------
        # UNKNOWN
        # -------------------------------------------------

        return (
            f"I don't know how to handle: {command}"
        )

    # =====================================================
    # CONFIRMATION
    # =====================================================

    def _request_confirmation(self, action: str) -> str:
        """
        Put a destructive system action into a pending
        confirmation state.
        """

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
                "Type 'yes', 'sure', or 'ok' to confirm.\n"
                "Type 'cancel' to abort."
            )

        self.pending_action = None

        return "This action requires confirmation."

    def _handle_confirmation(self, command: str) -> str:
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

            # Clear pending state BEFORE execution.
            self.pending_action = None

            return self._execute_confirmed_action(
                action
            )

        # -------------------------------------------------
        # INVALID RESPONSE
        # -------------------------------------------------

        return (
            "Confirmation required.\n"
            "Type 'yes', 'sure', or 'ok' to continue.\n"
            "Type 'cancel' to abort."
        )

    def _execute_confirmed_action(
        self,
        action: str,
    ) -> str:
        """Execute an already-confirmed system action."""

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
        """Handle screenshot request."""

        try:
            from tools.screenshot_tools import (
                ScreenshotTool,
            )

            tool = ScreenshotTool()

            return tool.take_screenshot()

        except Exception as error:
            return (
                f"Screenshot tool unavailable: {error}"
            )

    # =====================================================
    # FILE OPERATIONS
    # =====================================================

    def _handle_file_operation(
        self,
        operation: str,
        target: str,
    ) -> str:
        """
        Handle file operations through file_tools.
        """

        try:
            from tools.file_tools import FileTools

            tool = FileTools()

            if operation == "create":
                return tool.create_file(target)

            if operation == "read":
                return tool.read_file(target)

            if operation == "delete":
                return tool.delete_file(target)

            if operation == "search":
                return tool.search_file(target)

            if operation == "copy":
                source, destination = target.split(
                    "|",
                    1,
                )

                return tool.copy_file(
                    source,
                    destination,
                )

            if operation == "move":
                source, destination = target.split(
                    "|",
                    1,
                )

                return tool.move_file(
                    source,
                    destination,
                )

            if operation == "rename":
                source, new_name = target.split(
                    "|",
                    1,
                )

                return tool.rename_file(
                    source,
                    new_name,
                )

            return (
                f"Unsupported file operation: "
                f"{operation}"
            )

        except Exception as error:
            return (
                f"File operation failed: {error}"
            )