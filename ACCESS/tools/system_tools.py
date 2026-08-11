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

        aliases = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "calculator": "Calculator",
            "calc": "Calculator",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "visual studio code": "Visual Studio Code",
            "terminal": "Terminal",
            "safari": "Safari",
            "finder": "Finder",
        }

        requested_name = application_name

        application_name = aliases.get(
            application_name.lower(),
            application_name
        )

        try:

            if self.system == "Darwin":

                result = subprocess.run(
                    ["open", "-a", application_name],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    return (
                        f"I couldn't find an application named "
                        f"'{requested_name}'."
                    )

            elif self.system == "Windows":

                subprocess.Popen(
                    [
                        "cmd",
                        "/c",
                        "start",
                        "",
                        application_name
                    ]
                )

            else:
                return (
                    "This operating system is "
                    "not supported yet."
                )

            return f"Opening {application_name}."

        except Exception as error:

            return (
                f"I couldn't open {requested_name}. "
                f"Error: {error}"
            )