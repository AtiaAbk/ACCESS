from core.router import IntentRouter
from tools.system_tools import SystemTools


class AccessEngine:
    """
    Core execution engine of ACCESS.

    Receives user input, detects intent through the router,
    and executes the appropriate system tool.
    """

    def __init__(self):
        self.running = True
        self.router = IntentRouter()
        self.system_tools = SystemTools()

    def process(self, user_input: str) -> str:
        """Process a user command."""

        intent = self.router.route(user_input)

        # Empty input
        if intent.name == "empty":
            return "I didn't receive any command."

        # Exit
        if intent.name == "exit":
            self.stop()
            return "Session terminated safely."

        # Open application
        if intent.name == "open_application":
            return self.system_tools.open_application(
                intent.target
            )

        # Unknown command
        if intent.name == "unknown":
            return (
                f"I don't know how to handle: "
                f"{intent.target}"
            )

        return "I couldn't determine what to do."

    def stop(self):
        """Stop ACCESS."""

        self.running = False