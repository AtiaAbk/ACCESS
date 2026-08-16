from datetime import datetime
from pathlib import Path


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
        """Capture the entire screen."""

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

            return f"Screenshot saved to {output_file}"

        except ImportError:
            return (
                "Screenshot requires pyautogui. "
                "Install it with: pip install pyautogui"
            )

        except Exception as error:
            return f"Unable to capture screenshot: {error}"
