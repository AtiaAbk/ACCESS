from tools.system_tools import SystemTools


class AccessEngine:
    """
    Core engine of ACCESS.

    Responsible for receiving user input,
    understanding basic commands,
    and executing appropriate tools.
    """

    def __init__(self):
        self.running = True
        self.system_tools = SystemTools()

    def process(self, user_input: str) -> str:
        """Process a user command."""

        command = user_input.strip()

        if not command:
            return "I didn't receive any command."

        command_lower = command.lower()

        # Open application
        if command_lower.startswith("open "):
            application_name = command[5:].strip()

            return self.system_tools.open_application(
                application_name
            )

        return f"You said: {command}"

    def stop(self):
        """Stop ACCESS."""

        self.running = False