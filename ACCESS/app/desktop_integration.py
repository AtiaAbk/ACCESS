"""Optional system tray, desktop notification, and global-hotkey support."""

from __future__ import annotations

import platform
import threading
from collections.abc import Callable


class DesktopIntegration:
    """Bridge platform integrations to a thread-safe GUI event callback."""

    def __init__(self, emit: Callable[[str], None]):
        self.emit = emit
        self.tray_icon = None
        self.hotkey_listener = None

    def start(self, hotkey_enabled: bool = True, tray_enabled: bool = True) -> None:
        self.configure_tray(tray_enabled)
        self.configure_hotkey(hotkey_enabled)

    def configure_tray(self, enabled: bool) -> None:
        if not enabled:
            if self.tray_icon is not None:
                try:
                    self.tray_icon.stop()
                except Exception:
                    pass
                self.tray_icon = None
            return
        if self.tray_icon is None:
            self._start_tray()

    def _start_tray(self) -> None:
        try:
            import pystray
            from PIL import Image, ImageDraw

            image = Image.new("RGB", (64, 64), "#07111F")
            draw = ImageDraw.Draw(image)
            draw.rounded_rectangle((5, 5, 59, 59), radius=9, fill="#08D4C4")
            draw.text((21, 13), "A", fill="#07111F", stroke_width=1)
            menu = pystray.Menu(
                pystray.MenuItem(
                    "Open ACCESS",
                    lambda _icon, _item: self.emit("show"),
                    default=True,
                ),
                pystray.MenuItem(
                    "Talk to ACCESS", lambda _icon, _item: self.emit("voice")
                ),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", lambda _icon, _item: self.emit("quit")),
            )
            self.tray_icon = pystray.Icon("ACCESS", image, "ACCESS", menu)
            if platform.system() == "Darwin":
                self.tray_icon.run_detached()
            else:
                threading.Thread(
                    target=self.tray_icon.run,
                    name="access-tray",
                    daemon=True,
                ).start()
        except Exception:
            self.tray_icon = None

    def configure_hotkey(self, enabled: bool) -> None:
        if self.hotkey_listener is not None:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
            self.hotkey_listener = None
        if not enabled:
            return
        try:
            from pynput import keyboard

            self.hotkey_listener = keyboard.GlobalHotKeys(
                {"<ctrl>+<alt>+<space>": lambda: self.emit("voice")}
            )
            self.hotkey_listener.start()
        except Exception:
            self.hotkey_listener = None

    def notify(self, title: str, message: str) -> bool:
        try:
            if self.tray_icon is not None and self.tray_icon.HAS_NOTIFICATION:
                self.tray_icon.notify(message, title)
                return True
        except Exception:
            pass
        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                app_name="ACCESS",
                timeout=10,
            )
            return True
        except Exception:
            return False

    @property
    def tray_available(self) -> bool:
        return self.tray_icon is not None

    @property
    def hotkey_available(self) -> bool:
        return self.hotkey_listener is not None

    def stop(self) -> None:
        self.configure_hotkey(False)
        self.configure_tray(False)
