import platform
import subprocess


class SystemTools:
    """Tools for controlling the local operating system."""

    def __init__(self):
        self.system = platform.system()

    def _get_application_name(self, application_name: str) -> tuple[str, str]:
        """Resolve common application aliases."""

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

        requested_name = application_name.strip()

        resolved_name = aliases.get(
            requested_name.lower(),
            requested_name,
        )

        return requested_name, resolved_name

    def open_application(self, application_name: str) -> str:
        """Open an installed desktop application."""

        application_name = application_name.strip()

        if not application_name:
            return "Please specify an application."

        requested_name, resolved_name = (
            self._get_application_name(application_name)
        )

        try:
            if self.system == "Darwin":
                result = subprocess.run(
                    ["open", "-a", resolved_name],
                    capture_output=True,
                    text=True,
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
                        resolved_name,
                    ]
                )

            else:
                return (
                    "This operating system is "
                    "not supported yet."
                )

            return f"Opening {resolved_name}."

        except Exception as error:
            return (
                f"I couldn't open {requested_name}. "
                f"Error: {error}"
            )

    def close_application(self, application_name: str) -> str:
        """Close a running desktop application."""

        application_name = application_name.strip()

        if not application_name:
            return "Please specify an application."

        requested_name, resolved_name = (
            self._get_application_name(application_name)
        )

        try:
            if self.system == "Darwin":
                script = (
                    f'tell application "{resolved_name}" '
                    f"to quit"
                )

                result = subprocess.run(
                    ["osascript", "-e", script],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    return (
                        f"I couldn't close "
                        f"'{requested_name}'."
                    )

            elif self.system == "Windows":
                executable_names = {
                    "Google Chrome": "chrome.exe",
                    "Calculator": "CalculatorApp.exe",
                    "Visual Studio Code": "Code.exe",
                    "Terminal": "WindowsTerminal.exe",
                    "Safari": "Safari.exe",
                }

                executable = executable_names.get(
                    resolved_name,
                    f"{resolved_name}.exe",
                )

                result = subprocess.run(
                    [
                        "taskkill",
                        "/IM",
                        executable,
                        "/F",
                    ],
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    return (
                        f"I couldn't close "
                        f"'{requested_name}'."
                    )

            else:
                return (
                    "This operating system is "
                    "not supported yet."
                )

            return f"Closing {resolved_name}."

        except Exception as error:
            return (
                f"I couldn't close {requested_name}. "
                f"Error: {error}"
            )