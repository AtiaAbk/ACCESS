import platform
import shutil
import subprocess


class SystemControl:
    """Cross-platform system control tools."""

    def __init__(self):
        self.system = platform.system()

    # =====================================================
    # APPLICATION CONTROL
    # =====================================================

    def open_application(self, application_name: str) -> str:
        """Open an application."""

        if not application_name:
            return "Please specify an application."

        application_name = application_name.strip()

        try:
            if self.system == "Darwin":
                check = subprocess.run(
                    ["pgrep", "-x", application_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                if check.returncode == 0:
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
                        "Bringing it to the foreground."
                    )

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
                subprocess.Popen([application_name])
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
        """Close an application gracefully where possible."""

        if not application_name:
            return "Please specify an application."

        application_name = application_name.strip()

        try:
            if self.system == "Darwin":
                check = subprocess.run(
                    ["pgrep", "-x", application_name],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                if check.returncode != 0:
                    return f"{application_name} is not currently open."

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
                    ["taskkill", "/IM", f"{application_name}.exe"],
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
                        "set currentVolume to output volume of (get volume settings)",
                        "-e",
                        "set volume output volume (currentVolume + 10)",
                    ],
                    check=True,
                )
                return "Volume increased."

            if self.system == "Windows":
                return (
                    "Volume control is not implemented "
                    "for Windows yet."
                )

            if self.system == "Linux":
                return (
                    "Volume control is not implemented "
                    "for Linux yet."
                )

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
                        "set currentVolume to output volume of (get volume settings)",
                        "-e",
                        "set volume output volume (currentVolume - 10)",
                    ],
                    check=True,
                )
                return "Volume decreased."

            if self.system == "Windows":
                return (
                    "Volume control is not implemented "
                    "for Windows yet."
                )

            if self.system == "Linux":
                return (
                    "Volume control is not implemented "
                    "for Linux yet."
                )

            return "Volume control is not supported on this system."

        except Exception as error:
            return f"Unable to change volume: {error}"

    def mute(self) -> str:
        """Toggle system mute."""

        try:
            if self.system == "Darwin":
                current_state = subprocess.run(
                    [
                        "osascript",
                        "-e",
                        "output muted of (get volume settings)",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )

                is_muted = (
                    current_state.stdout.strip().lower() == "true"
                )

                new_state = "false" if is_muted else "true"

                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f"set volume output muted {new_state}",
                    ],
                    check=True,
                )

                if new_state == "true":
                    return "System audio muted."

                return "System audio unmuted."

            if self.system == "Windows":
                return (
                    "Mute control is not implemented "
                    "for Windows yet."
                )

            if self.system == "Linux":
                return (
                    "Mute control is not implemented "
                    "for Linux yet."
                )

            return "Mute control is not supported on this system."

        except Exception as error:
            return f"Unable to toggle mute: {error}"

    # =====================================================
    # BRIGHTNESS
    # =====================================================

    def _change_brightness(self, direction: str) -> str:
        """Change brightness when supported by the platform."""

        if self.system == "Darwin":

            if shutil.which("brightness") is None:
                return (
                    "I don't have permission to control "
                    "brightness because the required "
                    "'brightness' utility is unavailable."
                )

            try:
                delta = "+0.1" if direction == "up" else "-0.1"

                subprocess.run(
                    ["brightness", delta],
                    check=True,
                )

                if direction == "up":
                    return "Brightness increased."

                return "Brightness decreased."

            except subprocess.CalledProcessError:
                return (
                    "I don't have permission to change "
                    "the brightness."
                )

            except Exception:
                return (
                    "I don't have permission to change "
                    "the brightness."
                )

        if self.system in {"Windows", "Linux"}:
            return (
                f"I don't have permission to control "
                f"brightness on {self.system}."
            )

        return (
            "I don't have permission to control "
            "brightness on this system."
        )

    def brightness_up(self) -> str:
        """Increase display brightness."""
        return self._change_brightness("up")

    def brightness_down(self) -> str:
        """Decrease display brightness."""
        return self._change_brightness("down")

    # =====================================================
    # APPEARANCE / DARK MODE
    # =====================================================

    def dark_mode(self) -> str:
        """Enable system dark appearance."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to tell appearance preferences to set dark mode to true',
                    ],
                    check=True,
                )

                return "Dark mode enabled."

            if self.system == "Windows":
                return (
                    "I don't have permission to change "
                    "the system appearance on Windows."
                )

            if self.system == "Linux":
                return (
                    "I don't have permission to change "
                    "the system appearance on Linux."
                )

            return (
                "I don't have permission to change "
                "the system appearance on this system."
            )

        except subprocess.CalledProcessError:
            return (
                "I don't have permission to enable dark mode."
            )

        except Exception:
            return (
                "I don't have permission to enable dark mode."
            )

    def light_mode(self) -> str:
        """Enable system light appearance."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to tell appearance preferences to set dark mode to false',
                    ],
                    check=True,
                )

                return "Light mode enabled."

            if self.system == "Windows":
                return (
                    "I don't have permission to change "
                    "the system appearance on Windows."
                )

            if self.system == "Linux":
                return (
                    "I don't have permission to change "
                    "the system appearance on Linux."
                )

            return (
                "I don't have permission to change "
                "the system appearance on this system."
            )

        except subprocess.CalledProcessError:
            return (
                "I don't have permission to enable light mode."
            )

        except Exception:
            return (
                "I don't have permission to enable light mode."
            )

    # =====================================================
    # POWER STATUS
    # =====================================================

    def shutdown(self) -> str:
        """Return shutdown status without executing it."""

        if self.system in {"Darwin", "Windows", "Linux"}:
            return (
                "Shutdown command is available "
                "but requires confirmation."
            )

        return "Shutdown is not supported on this system."

    def restart(self) -> str:
        """Return restart status without executing it."""

        if self.system in {"Darwin", "Windows", "Linux"}:
            return (
                "Restart command is available "
                "but requires confirmation."
            )

        return "Restart is not supported on this system."

    # =====================================================
    # CONFIRMED POWER ACTIONS
    # =====================================================

    def execute_shutdown(self) -> str:
        """Execute shutdown after confirmation."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to shut down',
                    ],
                    check=True,
                )
                return "Shutting down the computer."

            if self.system == "Windows":
                subprocess.run(
                    ["shutdown", "/s", "/t", "0"],
                    check=True,
                )
                return "Shutting down the computer."

            if self.system == "Linux":
                subprocess.run(
                    ["systemctl", "poweroff"],
                    check=True,
                )
                return "Shutting down the computer."

            return "Shutdown is not supported on this system."

        except Exception as error:
            return f"Unable to shut down: {error}"

    def execute_restart(self) -> str:
        """Execute restart after confirmation."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        'tell application "System Events" to restart',
                    ],
                    check=True,
                )
                return "Restarting the computer."

            if self.system == "Windows":
                subprocess.run(
                    ["shutdown", "/r", "/t", "0"],
                    check=True,
                )
                return "Restarting the computer."

            if self.system == "Linux":
                subprocess.run(
                    ["systemctl", "reboot"],
                    check=True,
                )
                return "Restarting the computer."

            return "Restart is not supported on this system."

        except Exception as error:
            return f"Unable to restart: {error}"

    def execute_sleep(self) -> str:
        """Put the computer to sleep after confirmation."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    ["pmset", "sleepnow"],
                    check=True,
                )
                return "Putting the computer to sleep."

            if self.system == "Windows":
                subprocess.run(
                    [
                        "powershell",
                        "-NoProfile",
                        "-Command",
                        (
                            "Add-Type -AssemblyName System.Windows.Forms; "
                            "[System.Windows.Forms.Application]::SetSuspendState("
                            "'Suspend', $false, $false)"
                        ),
                    ],
                    check=True,
                )
                return "Putting the computer to sleep."

            if self.system == "Linux":
                subprocess.run(
                    ["systemctl", "suspend"],
                    check=True,
                )
                return "Putting the computer to sleep."

            return "Sleep is not supported on this system."

        except Exception as error:
            return f"Unable to put the computer to sleep: {error}"