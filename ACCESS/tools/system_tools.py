import platform
import subprocess


class SystemControl:
    """Cross-platform system control tools."""

    def __init__(self):
        self.system = platform.system()

    # =====================================================
    # APPLICATION CONTROL
    # =====================================================

    def open_application(self, application_name: str) -> str:
        """
        Open an application.

        On macOS, if the application is already running,
        bring it to the foreground instead of returning an error.
        """

        if not application_name:
            return "Please specify an application."

        application_name = application_name.strip()

        try:
            if self.system == "Darwin":

                # Check whether the application is already running
                check = subprocess.run(
                    [
                        "pgrep",
                        "-x",
                        application_name,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                if check.returncode == 0:
                    # Application is already running.
                    # Bring it to the foreground.
                    subprocess.run(
                        [
                            "osascript",
                            "-e",
                            f'tell application "{application_name}" to activate',
                        ],
                        check=True,
                    )

                    return (
                        f"{application_name} is already open. "
                        f"Bringing it to the foreground."
                    )

                # Application is not running.
                subprocess.run(
                    ["open", "-a", application_name],
                    check=True,
                )

                return f"Opening {application_name}."

            if self.system == "Windows":
                subprocess.Popen(
                    ["cmd", "/c", "start", "", application_name]
                )
                return f"Opening {application_name}."

            if self.system == "Linux":
                subprocess.Popen(
                    [application_name]
                )
                return f"Opening {application_name}."

            return (
                f"Opening applications is not supported "
                f"on {self.system}."
            )

        except FileNotFoundError:
            return f"Application not found: {application_name}"

        except subprocess.CalledProcessError as error:
            return f"Unable to open {application_name}: {error}"

        except Exception as error:
            return f"Unable to open {application_name}: {error}"

    def close_application(self, application_name: str) -> str:
        """
        Close an application.

        On macOS, request the application to quit gracefully.
        """

        if not application_name:
            return "Please specify an application."

        application_name = application_name.strip()

        try:
            if self.system == "Darwin":

                # Check whether the application is running.
                check = subprocess.run(
                    [
                        "pgrep",
                        "-x",
                        application_name,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                if check.returncode != 0:
                    return f"{application_name} is not currently open."

                # Ask macOS application to quit gracefully.
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'tell application "{application_name}" to quit',
                    ],
                    check=True,
                )

                return f"Closed {application_name}."

            if self.system == "Windows":
                subprocess.run(
                    [
                        "taskkill",
                        "/IM",
                        f"{application_name}.exe",
                    ],
                    check=True,
                )
                return f"Closed {application_name}."

            if self.system == "Linux":
                subprocess.run(
                    ["pkill", "-x", application_name],
                    check=True,
                )
                return f"Closed {application_name}."

            return (
                f"Closing applications is not supported "
                f"on {self.system}."
            )

        except subprocess.CalledProcessError:
            return f"Unable to close {application_name}."

        except Exception as error:
            return f"Unable to close {application_name}: {error}"

    # =====================================================
    # SCREEN LOCK
    # =====================================================

    def lock_screen(self) -> str:
        """Lock the current computer."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to keystroke "q" using {control down, command down}',
                    ],
                    check=True,
                )
                return "Locking the screen."

            if self.system == "Windows":
                subprocess.run(
                    [
                        "rundll32.exe",
                        "user32.dll,LockWorkStation",
                    ],
                    check=True,
                )
                return "Locking the screen."

            if self.system == "Linux":
                subprocess.run(
                    ["loginctl", "lock-session"],
                    check=True,
                )
                return "Locking the screen."

            return "Screen locking is not supported on this system."

        except Exception as error:
            return f"Unable to lock screen: {error}"

    # =====================================================
    # VOLUME
    # =====================================================

    def volume_up(self) -> str:
        """Increase system volume."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        "set volume output volume ((output volume of (get volume settings)) + 10)",
                    ],
                    check=True,
                )
                return "Volume increased."

            if self.system == "Windows":
                return "Windows volume control will be added next."

            if self.system == "Linux":
                return "Linux volume control will be added next."

            return "Volume control is not supported on this system."

        except Exception as error:
            return f"Unable to change volume: {error}"

    def volume_down(self) -> str:
        """Decrease system volume."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        "set volume output volume ((output volume of (get volume settings)) - 10)",
                    ],
                    check=True,
                )
                return "Volume decreased."

            if self.system == "Windows":
                return "Windows volume control will be added next."

            if self.system == "Linux":
                return "Linux volume control will be added next."

            return "Volume control is not supported on this system."

        except Exception as error:
            return f"Unable to change volume: {error}"

    def mute(self) -> str:
        """Toggle system mute."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        "set volume with output muted not (output muted of (get volume settings))",
                    ],
                    check=True,
                )
                return "Mute state toggled."

            if self.system == "Windows":
                return "Windows mute control will be added next."

            if self.system == "Linux":
                return "Linux mute control will be added next."

            return "Mute control is not supported on this system."

        except Exception as error:
            return f"Unable to toggle mute: {error}"

    # =====================================================
    # POWER
    # =====================================================

    def shutdown(self) -> str:
        """Return shutdown status without executing shutdown."""

        if self.system == "Darwin":
            return "Shutdown command is available but requires confirmation."

        if self.system == "Windows":
            return "Shutdown command is available but requires confirmation."

        if self.system == "Linux":
            return "Shutdown command is available but requires confirmation."

        return "Shutdown is not supported on this system."

    def restart(self) -> str:
        """Return restart status without executing restart."""

        if self.system == "Darwin":
            return "Restart command is available but requires confirmation."

        if self.system == "Windows":
            return "Restart command is available but requires confirmation."

        if self.system == "Linux":
            return "Restart command is available but requires confirmation."

        return "Restart is not supported on this system."