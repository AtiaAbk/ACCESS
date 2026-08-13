import os
import platform
import shutil
import subprocess
from pathlib import Path


class SystemControl:
    """Cross-platform system control tools."""

    def __init__(self):
        self.system = platform.system()

    # =====================================================
    # APPLICATION CONTROL
    # =====================================================

    WINDOWS_APPLICATION_ALIASES = {
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "notepad": "notepad.exe",
        "terminal": "wt.exe",
        "windows terminal": "wt.exe",
        "command prompt": "cmd.exe",
        "cmd": "cmd.exe",
        "visual studio code": "code.cmd",
        "vs code": "code.cmd",
        "vscode": "code.cmd",
        "google chrome": "chrome.exe",
        "chrome": "chrome.exe",
        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",
        "files": "explorer.exe",
        "task manager": "taskmgr.exe",
        "taskmgr": "taskmgr.exe",
        "paint": "mspaint.exe",
    }

    MAC_APPLICATION_ALIASES = {
        "file explorer": "Finder",
        "explorer": "Finder",
        "files": "Finder",
        "notepad": "TextEdit",
        "task manager": "Activity Monitor",
        "taskmgr": "Activity Monitor",
        "paint": "Preview",
        "vscode": "Visual Studio Code",
        "vs code": "Visual Studio Code",
        "chrome": "Google Chrome",
    }

    LINUX_APPLICATION_CANDIDATES = {
        "calculator": ("gnome-calculator", "kcalc", "galculator", "mate-calc", "xcalc"),
        "calc": ("gnome-calculator", "kcalc", "galculator", "mate-calc", "xcalc"),
        "google chrome": ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"),
        "chrome": ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"),
        "visual studio code": ("code", "codium"),
        "vscode": ("code", "codium"),
        "vs code": ("code", "codium"),
        "terminal": ("x-terminal-emulator", "gnome-terminal", "konsole", "xfce4-terminal", "xterm"),
        "notepad": ("gedit", "kate", "mousepad", "xed", "leafpad"),
        "task manager": ("gnome-system-monitor", "plasma-systemmonitor", "xfce4-taskmanager", "mate-system-monitor"),
        "taskmgr": ("gnome-system-monitor", "plasma-systemmonitor", "xfce4-taskmanager", "mate-system-monitor"),
        "paint": ("pinta", "kolourpaint", "drawing"),
    }

    @classmethod
    def _resolve_windows_application(cls, application_name: str) -> str | None:
        """Return a launchable Windows executable or path.

        Friendly display names such as ``Calculator`` are not valid executable
        names. Resolve known aliases first, then PATH, App Paths, and the common
        Chrome install locations. Returning ``None`` avoids Windows displaying a
        misleading asynchronous "cannot find" dialog after ACCESS reports success.
        """

        requested = application_name.strip()
        executable = cls.WINDOWS_APPLICATION_ALIASES.get(
            requested.casefold(), requested
        )

        requested_path = Path(os.path.expandvars(os.path.expanduser(executable)))
        if requested_path.is_file():
            return str(requested_path)

        resolved = shutil.which(executable)
        if resolved:
            return resolved

        if executable.casefold() == "chrome.exe":
            roots = [
                os.environ.get("PROGRAMFILES"),
                os.environ.get("PROGRAMFILES(X86)"),
                os.environ.get("LOCALAPPDATA"),
            ]
            for root in filter(None, roots):
                candidate = Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"
                if candidate.is_file():
                    return str(candidate)

        # Windows registers many desktop applications here even when they are
        # absent from PATH. Import winreg lazily to preserve cross-platform use.
        try:
            import winreg

            registry_keys = (
                (winreg.HKEY_CURRENT_USER, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{executable}"),
                (winreg.HKEY_LOCAL_MACHINE, rf"Software\Microsoft\Windows\CurrentVersion\App Paths\{executable}"),
            )
            for hive, key_name in registry_keys:
                try:
                    with winreg.OpenKey(hive, key_name) as key:
                        value, _ = winreg.QueryValueEx(key, None)
                    if value and Path(value).is_file():
                        return value
                except OSError:
                    continue
        except ImportError:
            pass

        return None

    @classmethod
    def _resolve_linux_application(cls, application_name: str) -> list[str] | None:
        """Resolve friendly names across common Linux desktop environments."""

        requested = application_name.strip()
        if requested.casefold() in {"file explorer", "explorer", "files"}:
            opener = shutil.which("xdg-open")
            return [opener, str(Path.home())] if opener else None

        candidates = cls.LINUX_APPLICATION_CANDIDATES.get(
            requested.casefold(),
            (requested,),
        )
        for candidate in candidates:
            executable = shutil.which(candidate)
            if executable:
                return [executable]
        return None

    def open_application(self, application_name: str) -> str:
        """Open an application."""

        if not application_name:
            return "Please specify an application."

        application_name = application_name.strip()

        try:
            if self.system == "Darwin":
                application_name = self.MAC_APPLICATION_ALIASES.get(
                    application_name.casefold(), application_name
                )
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
                launch_target = self._resolve_windows_application(application_name)
                if launch_target is None:
                    return (
                        f"Application not found: {application_name}. "
                        "Try its executable name or full path."
                    )
                subprocess.Popen([launch_target])
                return f"Opening {application_name}."

            if self.system == "Linux":
                launch_command = self._resolve_linux_application(application_name)
                if launch_command is None:
                    return (
                        f"Application not found: {application_name}. "
                        "Install it or use its executable name."
                    )
                subprocess.Popen(launch_command)
                return f"Opening {application_name}."

            return f"Opening applications is not supported on {self.system}."

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
                application_name = self.MAC_APPLICATION_ALIASES.get(
                    application_name.casefold(), application_name
                )
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
                launch_command = self._resolve_linux_application(application_name)
                if not launch_command or Path(launch_command[0]).name == "xdg-open":
                    return f"Unable to identify a running process for {application_name}."
                subprocess.run(["pkill", "-x", Path(launch_command[0]).name], check=True)
                return f"Closed {application_name}."

            return f"Closing applications is not supported on {self.system}."

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
                    ["rundll32.exe", "user32.dll,LockWorkStation"],
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
                return "Volume control is not implemented for Windows yet."

            if self.system == "Linux":
                return "Volume control is not implemented for Linux yet."

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
                return "Volume control is not implemented for Windows yet."

            if self.system == "Linux":
                return "Volume control is not implemented for Linux yet."

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
                return "Mute control is not implemented for Windows yet."

            if self.system == "Linux":
                return "Mute control is not implemented for Linux yet."

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
                    "Brightness control requires the 'brightness' "
                    "command-line utility on macOS."
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

            except subprocess.CalledProcessError as error:
                return f"Unable to change brightness: {error}"

        if self.system in {"Windows", "Linux"}:
            return f"Brightness control is not implemented for {self.system} yet."

        return "Brightness control is not supported on this system."

    def brightness_up(self) -> str:
        """Increase display brightness."""
        return self._change_brightness("up")

    def brightness_down(self) -> str:
        """Decrease display brightness."""
        return self._change_brightness("down")

    # =====================================================
    # POWER STATUS
    # =====================================================

    def shutdown(self) -> str:
        """Return shutdown status without executing it."""

        if self.system in {"Darwin", "Windows", "Linux"}:
            return "Shutdown command is available but requires confirmation."

        return "Shutdown is not supported on this system."

    def restart(self) -> str:
        """Return restart status without executing it."""

        if self.system in {"Darwin", "Windows", "Linux"}:
            return "Restart command is available but requires confirmation."

        return "Restart is not supported on this system."

    # =====================================================
    # CONFIRMED POWER ACTIONS
    # =====================================================

    def execute_shutdown(self) -> str:
        """Execute shutdown after confirmation."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    ["osascript", "-e", "tell application \"System Events\" to shut down"],
                    check=True,
                )
                return "Shutting down the computer."

            if self.system == "Windows":
                subprocess.run(["shutdown", "/s", "/t", "0"], check=True)
                return "Shutting down the computer."

            if self.system == "Linux":
                subprocess.run(["systemctl", "poweroff"], check=True)
                return "Shutting down the computer."

            return "Shutdown is not supported on this system."

        except Exception as error:
            return f"Unable to shut down: {error}"

    def execute_restart(self) -> str:
        """Execute restart after confirmation."""

        try:
            if self.system == "Darwin":
                subprocess.run(
                    ["osascript", "-e", "tell application \"System Events\" to restart"],
                    check=True,
                )
                return "Restarting the computer."

            if self.system == "Windows":
                subprocess.run(["shutdown", "/r", "/t", "0"], check=True)
                return "Restarting the computer."

            if self.system == "Linux":
                subprocess.run(["systemctl", "reboot"], check=True)
                return "Restarting the computer."

            return "Restart is not supported on this system."

        except Exception as error:
            return f"Unable to restart: {error}"

    def execute_sleep(self) -> str:
        """Put the computer to sleep after confirmation."""

        try:
            if self.system == "Darwin":
                subprocess.run(["pmset", "sleepnow"], check=True)
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
                subprocess.run(["systemctl", "suspend"], check=True)
                return "Putting the computer to sleep."

            return "Sleep is not supported on this system."

        except Exception as error:
            return f"Unable to put the computer to sleep: {error}"
