from datetime import datetime
from pathlib import Path
import platform
import subprocess


class ScreenshotTools:
    """Tools for capturing screenshots."""

    def __init__(self):

        self.screenshot_directory = (
            Path(__file__).resolve().parent.parent
            / "data"
            / "screenshots"
        )

        self.screenshot_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def capture_screen(self) -> str:
        """Capture the entire screen and open its folder."""

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_file = (
            self.screenshot_directory
            / f"screenshot_{timestamp}.png"
        )

        try:

            import pyautogui

            image = pyautogui.screenshot()

            image.save(output_file)

            self.open_screenshot_folder()

            return (
                f"Screenshot saved to "
                f"{output_file}"
            )

        except ImportError:

            return (
                "Screenshot requires pyautogui. "
                "Install it with: "
                "pip install pyautogui"
            )

        except Exception as error:

            return (
                f"Unable to capture screenshot: "
                f"{error}"
            )

    def open_screenshot_folder(self):
        """Open screenshot directory in the OS file manager."""

        try:

            system = platform.system()

            if system == "Darwin":

                subprocess.Popen(
                    [
                        "open",
                        str(self.screenshot_directory),
                    ]
                )

            elif system == "Windows":

                subprocess.Popen(
                    [
                        "explorer",
                        str(self.screenshot_directory),
                    ]
                )

            elif system == "Linux":

                subprocess.Popen(
                    [
                        "xdg-open",
                        str(self.screenshot_directory),
                    ]
                )

        except Exception:
            # Opening Finder/File Explorer should never
            # cause screenshot capture itself to fail.
            pass