class AccessEngine:
    """
    Core engine of ACCESS.

    Responsible for receiving user input
    and processing commands.
    """

    def __init__(self):
        self.running = True

    def process(self, user_input: str) -> str:
        """
        Process a user command.
        """

        command = user_input.strip()

        if not command:
            return "I didn't receive any command."

        return f"You said: {command}"

    def stop(self):
        """Stop ACCESS."""
        self.running = False