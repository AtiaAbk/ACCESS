import platform
import subprocess


class SystemTools:
    """Tools for controlling the local operating system."""

    def __init__(self):
        self.system = platform.system()

    def open_application(self, application_name: str) -> str:
        """Open an installed desktop application."""

        application_name = application_name.strip()

        if not application_name:
            return "Please specify an application."

        try:
            if self.system == "Darwin":
                subprocess.Popen(
                    ["open", "-a", application_name]
                )

            elif self.system == "Windows":
                subprocess.Popen(
                    ["cmd", "/c", "start", "", application_name],
                    shell=False
                )

            else:
                return "This operating system is not supported yet."

            return f"Opening {application_name}."

        except Exception as error:
            return (
                f"I couldn't open {application_name}. "
                f"Error: {error}"
            )
