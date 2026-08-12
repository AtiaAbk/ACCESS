
from tools.system_tools import SystemControl
from tools.screenshot_tools import ScreenshotTools
from tools.file_tools import FileTools


class AccessEngine:
    """
    Core execution engine of ACCESS.

    Responsible for receiving user commands
    and dispatching them to the appropriate tools.
    """

    def __init__(self):
        self.running = True

        self.system_tools = SystemControl()
        self.screenshot_tools = ScreenshotTools()
        self.file_tools = FileTools()

    def process(self, user_input: str) -> str:
        """Process and execute a user command."""

        command = user_input.strip()

        if not command:
            return "I didn't receive any command."

        command_lower = command.lower()

        # =====================================================
        # EXIT
        # =====================================================

        if command_lower in {
            "exit",
            "quit",
            "close access",
        }:
            self.stop()
            return "Session terminated safely."

        # =====================================================
        # SCREENSHOT
        # =====================================================

        if command_lower in {
            "take screenshot",
            "capture screenshot",
            "screenshot",
            "take a screenshot",
        }:
            return self.screenshot_tools.capture_screen()

        # =====================================================
        # OPEN APPLICATION
        # =====================================================

        if command_lower.startswith("open "):
            application_name = command[5:].strip()

            if not application_name:
                return "Please specify an application."

            return self.system_tools.open_application(
                application_name
            )
                # =====================================================
        # CLOSE APPLICATION
        # =====================================================

        if command_lower.startswith("close "):

            application_name = command[6:].strip()

            if not application_name:
                return "Please specify an application."

            return self.system_tools.close_application(
                application_name
            )
        # =====================================================
        # CREATE FILE
        # =====================================================

        if command_lower.startswith("create file "):

            file_path = command[12:].strip()

            if not file_path:
                return "Please specify a file name."

            return self.file_tools.create_file(
                file_path
            )

        # =====================================================
        # SEARCH FILE
        # =====================================================

        if command_lower.startswith("search file "):

            filename = command[12:].strip()

            if not filename:
                return "Please specify a file name."

            return self.file_tools.search_file(
                "data",
                filename
            )

        # =====================================================
        # COPY FILE
        # Format:
        # copy file SOURCE to DESTINATION
        # =====================================================

        if command_lower.startswith("copy file "):

            instruction = command[10:].strip()

            parts = instruction.lower().split(" to ", 1)

            if len(parts) != 2:
                return (
                    "Use: copy file SOURCE to DESTINATION"
                )

            source_part, destination_part = parts

            source = instruction[
                :len(source_part)
            ].strip()

            destination = instruction[
                len(source_part) + 4:
            ].strip()

            if not source or not destination:
                return (
                    "Use: copy file SOURCE to DESTINATION"
                )

            return self.file_tools.copy_file(
                source,
                destination
            )

        # =====================================================
        # MOVE FILE
        # Format:
        # move file SOURCE to DESTINATION
        # =====================================================

        if command_lower.startswith("move file "):

            instruction = command[10:].strip()

            parts = instruction.lower().split(" to ", 1)

            if len(parts) != 2:
                return (
                    "Use: move file SOURCE to DESTINATION"
                )

            source_part, destination_part = parts

            source = instruction[
                :len(source_part)
            ].strip()

            destination = instruction[
                len(source_part) + 4:
            ].strip()

            if not source or not destination:
                return (
                    "Use: move file SOURCE to DESTINATION"
                )

            return self.file_tools.move_file(
                source,
                destination
            )

        # =====================================================
        # RENAME FILE
        # Format:
        # rename file SOURCE to NEW_NAME
        # =====================================================

        if command_lower.startswith("rename file "):

            instruction = command[12:].strip()

            parts = instruction.lower().split(" to ", 1)

            if len(parts) != 2:
                return (
                    "Use: rename file SOURCE to NEW_NAME"
                )

            source_part, new_name_part = parts

            source = instruction[
                :len(source_part)
            ].strip()

            new_name = instruction[
                len(source_part) + 4:
            ].strip()

            if not source or not new_name:
                return (
                    "Use: rename file SOURCE to NEW_NAME"
                )

            return self.file_tools.rename_file(
                source,
                new_name
            )

        # =====================================================
        # UNKNOWN COMMAND
        # =====================================================

        return f"You said: {command}"

    def stop(self):
        """Stop ACCESS."""

        self.running = False
