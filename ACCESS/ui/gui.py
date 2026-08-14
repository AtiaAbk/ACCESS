"""Native desktop interface for ACCESS.

The UI deliberately depends only on tkinter so ACCESS can still start offline on a
fresh Python installation.  All assistant work is delegated to AccessEngine; this
module is only responsible for presentation and user interaction.
"""

from __future__ import annotations

import os
import platform
import queue
import json
import subprocess
import threading
import tkinter as tk
import tkinter.font as tkfont
import uuid
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from typing import Callable

from core.engine import AccessEngine
from ui.syntax_highlighter import HighlightedCode, highlight_code


APP_NAME = "ACCESS"
APP_SUBTITLE = "Adaptive Cognitive Companion for Efficient System Services"
VERSION = "1.0"

DEFAULT_WINDOW_SIZE = (1680, 945)
MINIMUM_WINDOW_SIZE = (960, 600)
WINDOW_MARGIN = (64, 48)


QUICK_ACTION_CATALOG = {
    "screenshot": {"icon": "\ue722", "label": "Screenshot", "kind": "command", "value": "take a screenshot"},
    "chrome": {"icon": "\ue774", "label": "Chrome", "kind": "command", "value": "open chrome"},
    "calculator": {"icon": "\ue8ef", "label": "Calculator", "kind": "command", "value": "open calculator"},
    "vscode": {"icon": "\ue943", "label": "VS Code", "kind": "command", "value": "open vscode"},
    "explorer": {"icon": "\ue8b7", "label": "Explorer", "kind": "command", "value": "open file explorer"},
    "terminal": {"icon": "\ue756", "label": "Terminal", "kind": "command", "value": "open terminal"},
    "notepad": {"icon": "\ue70f", "label": "Notepad", "kind": "command", "value": "open notepad"},
    "task_manager": {"icon": "\ue9d9", "label": "Task Mgr", "kind": "command", "value": "open task manager"},
    "paint": {"icon": "\ue790", "label": "Paint", "kind": "command", "value": "open paint"},
    "history": {"icon": "\ue81c", "label": "History", "kind": "ui", "value": "history"},
    "commands": {"icon": "\ue897", "label": "Commands", "kind": "ui", "value": "commands"},
    "new_chat": {"icon": "\ue8a7", "label": "New chat", "kind": "ui", "value": "new_chat"},
    "status": {"icon": "\ue9d2", "label": "Status", "kind": "command", "value": "status"},
    "about": {"icon": "\ue946", "label": "About", "kind": "command", "value": "about"},
    "sleep": {"icon": "\ue708", "label": "Sleep", "kind": "command", "value": "sleep"},
    "restart": {"icon": "\ue777", "label": "Restart", "kind": "command", "value": "restart"},
    "lock": {"icon": "\ue72e", "label": "Lock", "kind": "command", "value": "lock screen"},
}

DEFAULT_QUICK_ACTIONS = [
    "screenshot", "chrome", "calculator", "vscode", "explorer", "terminal",
    "notepad", "task_manager", "history", "commands", "new_chat", "lock", "paint",
]

FALLBACK_ACTION_ICONS = {
    "screenshot": "▣", "chrome": "◎", "calculator": "∑", "vscode": "</>",
    "explorer": "▰", "terminal": ">_", "notepad": "✎", "task_manager": "≋",
    "paint": "✦", "history": "↶", "commands": "?", "new_chat": "+",
    "status": "◉", "about": "ⓘ", "sleep": "◐", "restart": "↻", "lock": "◆",
}


THEMES = {
    "dark": {
        "bg": "#07111F",
        "sidebar": "#091525",
        "surface": "#0D1A2C",
        "surface_2": "#102036",
        "border": "#29405C",
        "text": "#F6F8FC",
        "muted": "#9AA9C2",
        "accent": "#08D4C4",
        "accent_hover": "#00BDAF",
        "blue": "#2684FF",
        "user": "#175CD3",
        "success": "#08D4C4",
        "danger": "#FB7185",
        "input": "#0B182A",
        "code_bg": "#071321",
        "code_text": "#D4D4D4",
        "code_comment": "#6A9955",
        "code_keyword": "#D98BD8",
        "code_string": "#E7A278",
        "code_number": "#B5CEA8",
        "code_function": "#E4D27A",
        "code_type": "#4EC9B0",
        "code_preprocessor": "#C586C0",
    },
    "light": {
        "bg": "#F8FAFC",
        "sidebar": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface_2": "#F4F8FC",
        "border": "#D7E1EB",
        "text": "#08162D",
        "muted": "#60718D",
        "accent": "#00A99D",
        "accent_hover": "#00958A",
        "blue": "#2088F5",
        "user": "#2674E8",
        "success": "#08AE73",
        "danger": "#E14C66",
        "input": "#FFFFFF",
        "code_bg": "#F2F6FA",
        "code_text": "#263247",
        "code_comment": "#39814D",
        "code_keyword": "#8B3FA2",
        "code_string": "#A65325",
        "code_number": "#267F6C",
        "code_function": "#795E26",
        "code_type": "#167C80",
        "code_preprocessor": "#9C3D84",
    },
}


class RoundedPanel(tk.Canvas):
    """A responsive rounded container with a normal Frame for child widgets."""

    def __init__(
        self,
        parent: tk.Widget,
        panel_bg: str,
        border: str,
        radius: int = 14,
        border_width: int = 1,
        **kwargs,
    ):
        super().__init__(parent, bg=parent.cget("bg"), bd=0, highlightthickness=0, **kwargs)
        self.panel_bg = panel_bg
        self.border = border
        self.radius = radius
        self.border_width = border_width
        self.body = tk.Frame(self, bg=panel_bg)
        self._body_window = self.create_window((border_width + 1, border_width + 1), window=self.body, anchor="nw")
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None) -> None:
        width = max(2, self.winfo_width())
        height = max(2, self.winfo_height())
        radius = min(self.radius, width // 2, height // 2)
        self.delete("panel_shape")
        points = [
            radius, 1, width - radius, 1, width - 1, 1,
            width - 1, radius, width - 1, height - radius,
            width - 1, height - 1, width - radius, height - 1,
            radius, height - 1, 1, height - 1, 1, height - radius,
            1, radius, 1, 1,
        ]
        self.create_polygon(
            points,
            smooth=True,
            splinesteps=24,
            fill=self.panel_bg,
            outline=self.border,
            width=self.border_width,
            tags="panel_shape",
        )
        self.tag_lower("panel_shape")
        inset = max(5, self.border_width + 1)
        self.coords(self._body_window, inset, inset)
        self.itemconfigure(
            self._body_window,
            width=max(1, width - inset * 2),
            height=max(1, height - inset * 2),
        )


class AccessGUI:
    """Modern tkinter shell around :class:`AccessEngine`."""

    def __init__(self, root: tk.Tk | None = None, engine: AccessEngine | None = None):
        if platform.system() == "Windows":
            try:
                import ctypes

                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "ACCESS.DesktopAssistant.1"
                )
            except (AttributeError, OSError):
                pass
        self.root = root or tk.Tk()
        self.engine = engine or AccessEngine()
        self.theme_name = "dark"
        self.colors = THEMES[self.theme_name]
        self.busy = False
        self._chat_rows: list[tk.Widget] = []
        self._image_refs: list[object] = []
        self._results: queue.Queue[tuple[str, str]] = queue.Queue()
        available_fonts = set(tkfont.families(self.root))
        fluent_fonts = [
            name
            for name in ("Segoe Fluent Icons", "Segoe MDL2 Assets")
            if name in available_fonts
        ]
        self.has_fluent_icons = bool(fluent_fonts)
        self.icon_font_family = (
            fluent_fonts[0]
            if fluent_fonts
            else next(
                (name for name in ("Apple Symbols", "Noto Sans Symbols 2", "DejaVu Sans") if name in available_fonts),
                "TkDefaultFont",
            )
        )
        self.settings_path = self._settings_file()
        self.quick_action_items = self._load_quick_actions()

        self.root.title(f"{APP_NAME} — Desktop Assistant")
        initial_geometry, initial_size = self._initial_window_geometry()
        self.root.geometry(initial_geometry)
        self.root.minsize(
            min(MINIMUM_WINDOW_SIZE[0], initial_size[0]),
            min(MINIMUM_WINDOW_SIZE[1], initial_size[1]),
        )
        self.root.overrideredirect(True)
        self.root.configure(bg=self.colors["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.app_icon = self._create_app_icon()
        self.root.iconphoto(True, self.app_icon)
        self._drag_origin = (0, 0)
        self._restore_geometry = initial_geometry
        self._is_maximized = False

        self._configure_styles()
        self._build_layout()
        self._bind_shortcuts()
        self._add_welcome_message()
        self.root.after(50, self._poll_results)
        self.command_entry.focus_set()

    def _work_area(self) -> tuple[int, int, int, int]:
        """Return the usable desktop area as ``left, top, width, height``."""

        if platform.system() == "Windows":
            try:
                import ctypes
                from ctypes import wintypes

                work_area = wintypes.RECT()
                # SPI_GETWORKAREA excludes the taskbar and docked toolbars.
                if ctypes.windll.user32.SystemParametersInfoW(
                    0x0030, 0, ctypes.byref(work_area), 0
                ):
                    return (
                        work_area.left,
                        work_area.top,
                        work_area.right - work_area.left,
                        work_area.bottom - work_area.top,
                    )
            except (AttributeError, OSError):
                pass

        return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()

    def _initial_window_geometry(self) -> tuple[str, tuple[int, int]]:
        """Fit and center the default window within the usable desktop area."""

        left, top, work_width, work_height = self._work_area()
        margin_x, margin_y = WINDOW_MARGIN
        window_width = min(DEFAULT_WINDOW_SIZE[0], max(1, work_width - margin_x))
        window_height = min(DEFAULT_WINDOW_SIZE[1], max(1, work_height - margin_y))
        x = left + max(0, (work_width - window_width) // 2)
        y = top + max(0, (work_height - window_height) // 2)
        return (
            f"{window_width}x{window_height}+{x}+{y}",
            (window_width, window_height),
        )

    # ------------------------------------------------------------------ layout
    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Access.Vertical.TScrollbar",
            background=self.colors["surface_2"],
            troughcolor=self.colors["surface"],
            bordercolor=self.colors["surface"],
            arrowcolor=self.colors["muted"],
        )

    def _apply_native_titlebar_theme(self) -> None:
        """Match the Windows title bar to the selected reference theme."""

        if platform.system() != "Windows":
            return
        try:
            import ctypes

            self.root.update_idletasks()
            value = ctypes.c_int(1 if self.theme_name == "dark" else 0)
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            for attribute in (20, 19):
                result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd,
                    attribute,
                    ctypes.byref(value),
                    ctypes.sizeof(value),
                )
                if result == 0:
                    break
        except (AttributeError, OSError):
            pass

    def _build_layout(self) -> None:
        c = self.colors
        self.app_container = tk.Frame(
            self.root,
            bg=c["bg"],
            highlightthickness=1,
            highlightbackground=c["border"],
        )
        self.app_container.pack(fill="both", expand=True)
        self._build_titlebar()
        self.shell = tk.Frame(self.app_container, bg=c["bg"])
        self.shell.pack(fill="both", expand=True)
        self._build_sidebar()
        self._build_main()

    def _build_titlebar(self) -> None:
        c = self.colors
        titlebar = tk.Frame(
            self.app_container,
            height=49,
            bg=c["sidebar"],
            highlightthickness=1,
            highlightbackground=c["border"],
        )
        titlebar.pack(fill="x")
        titlebar.pack_propagate(False)
        icon = tk.Label(
            titlebar,
            text="A",
            width=2,
            bg=c["accent"],
            fg="#06110F",
            font=("Segoe UI", 10, "bold"),
        )
        icon.pack(side="left", padx=(28, 12), pady=10)
        title = tk.Label(
            titlebar,
            text="ACCESS — Desktop Assistant",
            bg=c["sidebar"],
            fg=c["text"],
            font=("Segoe UI", 10),
        )
        title.pack(side="left")

        def control(text: str, command: Callable, danger: bool = False) -> tk.Button:
            button = tk.Button(
                titlebar,
                text=text,
                command=command,
                width=5,
                relief="flat",
                bd=0,
                bg=c["sidebar"],
                activebackground=c["danger"] if danger else c["surface_2"],
                fg=c["text"],
                activeforeground="#FFFFFF" if danger else c["text"],
                font=("Segoe UI Symbol", 11),
                cursor="hand2",
            )
            button.pack(side="right", fill="y")
            return button

        control("×", self.close, danger=True)
        control("□", self._toggle_maximize)
        control("—", self._minimize_window)
        for widget in (titlebar, title, icon):
            widget.bind("<ButtonPress-1>", self._start_window_drag)
            widget.bind("<B1-Motion>", self._drag_window)
            widget.bind("<Double-Button-1>", lambda _event: self._toggle_maximize())

    def _start_window_drag(self, event) -> None:
        if self._is_maximized:
            return
        self._drag_origin = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def _drag_window(self, event) -> None:
        if self._is_maximized:
            return
        x = event.x_root - self._drag_origin[0]
        y = event.y_root - self._drag_origin[1]
        self.root.geometry(f"+{x}+{y}")

    def _toggle_maximize(self) -> None:
        if self._is_maximized:
            self.root.geometry(self._restore_geometry)
            self._is_maximized = False
            return
        self._restore_geometry = self.root.geometry()
        left, top, width, height = self._work_area()
        self.root.geometry(f"{width}x{height}+{left}+{top}")
        self._is_maximized = True

    def _minimize_window(self) -> None:
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", self._restore_borderless, add="+")

    def _restore_borderless(self, _event=None) -> None:
        if self.root.state() == "normal":
            self.root.after(10, lambda: self.root.overrideredirect(True))

    def _build_sidebar(self) -> None:
        c = self.colors
        self.sidebar = tk.Frame(
            self.shell,
            width=320,
            bg=c["sidebar"],
            highlightthickness=1,
            highlightbackground=c["border"],
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=c["sidebar"])
        brand.pack(fill="x", padx=30, pady=(22, 12))
        tk.Label(
            brand,
            text="A",
            width=2,
            height=1,
            bg=c["accent"],
            fg="#06110F",
            font=("Segoe UI", 22, "bold"),
        ).pack(side="left")
        brand_text = tk.Frame(brand, bg=c["sidebar"])
        brand_text.pack(side="left", padx=14)
        tk.Label(
            brand_text,
            text="ACCESS",
            bg=c["sidebar"],
            fg=c["text"],
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text="DESKTOP AI",
            bg=c["sidebar"],
            fg=c["accent"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")

        tk.Label(
            self.sidebar,
            text="WORKSPACE",
            bg=c["sidebar"],
            fg=c["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=34, pady=(0, 8))

        self._nav_button("✦", "Assistant", lambda: self.command_entry.focus_set(), active=True)
        self._nav_button("↻", "New conversation", self.clear_conversation)
        self._nav_button("◷", "History", self.show_history)
        self._nav_button("?", "Commands", self.show_help)

        bottom = tk.Frame(self.sidebar, bg=c["sidebar"])
        bottom.pack(side="bottom", fill="x", padx=22, pady=(8, 34))
        theme_btn = tk.Button(
            bottom,
            text="☼  Switch theme",
            command=self.toggle_theme,
            anchor="w",
            relief="flat",
            bd=0,
            padx=14,
            pady=11,
            bg=c["surface"],
            activebackground=c["surface_2"],
            fg=c["text"],
            activeforeground=c["text"],
            font=("Segoe UI", 10),
            cursor="hand2",
        )
        theme_btn.pack(fill="x")
        tk.Label(
            bottom,
            text=f"Offline-first  •  v{VERSION}",
            bg=c["sidebar"],
            fg=c["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", padx=12, pady=(14, 0))

        quick = tk.Frame(self.sidebar, bg=c["sidebar"])
        quick.pack(fill="both", expand=True, padx=(22, 17), pady=(20, 4))
        quick_header = tk.Frame(quick, bg=c["sidebar"])
        quick_header.pack(fill="x", padx=(6, 2), pady=(0, 8))
        tk.Label(
            quick_header,
            text="QUICK ACTIONS",
            bg=c["sidebar"],
            fg=c["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left")
        setup_button = tk.Button(
            quick_header,
            text="SETUP  ›",
            command=self.show_quick_action_setup,
            relief="flat",
            bd=0,
            padx=4,
            pady=1,
            bg=c["sidebar"],
            activebackground=c["surface_2"],
            fg=c["accent"],
            activeforeground=c["accent"],
            font=("Segoe UI", 7, "bold"),
            cursor="hand2",
        ).pack(side="right")

        quick_body = tk.Frame(quick, bg=c["sidebar"])
        quick_body.pack(fill="both", expand=True)
        self.quick_canvas = tk.Canvas(
            quick_body,
            bg=c["sidebar"],
            bd=0,
            highlightthickness=0,
        )
        quick_scrollbar = ttk.Scrollbar(
            quick_body,
            orient="vertical",
            command=self.quick_canvas.yview,
            style="Access.Vertical.TScrollbar",
        )
        self.quick_canvas.configure(yscrollcommand=quick_scrollbar.set)
        # The reference uses an unobtrusive wheel-scroll launcher without a
        # permanently visible scrollbar.
        self.quick_canvas.pack(side="left", fill="both", expand=True)
        self.quick_grid = tk.Frame(self.quick_canvas, bg=c["sidebar"])
        quick_window = self.quick_canvas.create_window((0, 0), window=self.quick_grid, anchor="nw")
        self.quick_grid.columnconfigure(0, weight=1, uniform="quick")
        self.quick_grid.columnconfigure(1, weight=1, uniform="quick")
        self.quick_grid.bind(
            "<Configure>",
            lambda _event: self.quick_canvas.configure(scrollregion=self.quick_canvas.bbox("all")),
        )
        self.quick_canvas.bind(
            "<Configure>",
            lambda event: self.quick_canvas.itemconfigure(quick_window, width=event.width),
        )
        self.quick_canvas.bind("<MouseWheel>", self._on_quick_mousewheel)
        self.quick_canvas.bind("<Button-4>", self._on_quick_mousewheel)
        self.quick_canvas.bind("<Button-5>", self._on_quick_mousewheel)

        self._render_quick_actions()

    def _nav_button(self, icon: str, label: str, command: Callable, active: bool = False) -> None:
        c = self.colors
        bg = c["surface_2"] if active else c["sidebar"]
        fg = c["accent"] if active else c["muted"]
        button = tk.Button(
            self.sidebar,
            text=f"{icon}   {label}",
            command=command,
            anchor="w",
            relief="flat",
            bd=0,
            padx=30,
            pady=8,
            bg=bg,
            activebackground=c["surface_2"],
            fg=fg,
            activeforeground=c["text"],
            font=("Segoe UI", 11, "bold" if active else "normal"),
            cursor="hand2",
        )
        button.pack(fill="x", padx=20, pady=0)

    @staticmethod
    def _settings_file() -> Path:
        system_name = platform.system()
        if system_name == "Windows":
            root = os.environ.get("APPDATA")
            if root:
                return Path(root) / "ACCESS" / "settings.json"
        elif system_name == "Darwin":
            return Path.home() / "Library" / "Application Support" / "ACCESS" / "settings.json"
        else:
            root = os.environ.get("XDG_CONFIG_HOME")
            if root:
                return Path(root) / "ACCESS" / "settings.json"
        return Path.home() / ".config" / "ACCESS" / "settings.json"

    @staticmethod
    def _catalog_action(action_id: str) -> dict | None:
        action = QUICK_ACTION_CATALOG.get(action_id)
        return {"id": action_id, **action} if action else None

    def _default_quick_actions(self) -> list[dict]:
        return [
            action
            for action_id in DEFAULT_QUICK_ACTIONS
            if (action := self._catalog_action(action_id)) is not None
        ]

    def _load_quick_actions(self) -> list[dict]:
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            stored_actions = data.get("quick_actions", [])
            if not isinstance(stored_actions, list):
                raise ValueError("quick_actions must be a list")
        except (OSError, ValueError, json.JSONDecodeError):
            return self._default_quick_actions()

        actions: list[dict] = []
        seen: set[str] = set()
        for stored in stored_actions[:24]:
            if not isinstance(stored, dict):
                continue
            action_id = str(stored.get("id", ""))
            if not action_id or action_id in seen:
                continue
            action = self._catalog_action(action_id)
            if action is None and action_id.startswith("custom:"):
                label = str(stored.get("label", "")).strip()[:18]
                command = str(stored.get("value", "")).strip()[:500]
                if label and command:
                    action = {
                        "id": action_id,
                        "icon": "\ue945",
                        "label": label,
                        "kind": "command",
                        "value": command,
                    }
            if action:
                actions.append(action)
                seen.add(action_id)
        return actions

    def _save_quick_actions(self, actions: list[dict]) -> bool:
        payload = {
            "quick_actions": [
                {
                    "id": action["id"],
                    **(
                        {"label": action["label"], "value": action["value"]}
                        if str(action["id"]).startswith("custom:")
                        else {}
                    ),
                }
                for action in actions
            ]
        }
        try:
            self.settings_path.parent.mkdir(parents=True, exist_ok=True)
            self.settings_path.write_text(
                json.dumps(payload, indent=2),
                encoding="utf-8",
            )
            return True
        except OSError as error:
            messagebox.showerror(
                "Unable to save quick actions",
                f"ACCESS could not save your layout:\n{error}",
                parent=self.root,
            )
            return False

    def _execute_quick_action(self, action: dict) -> None:
        if action.get("kind") == "command":
            self.submit_command(str(action.get("value", "")))
            return
        handlers = {
            "history": self.show_history,
            "commands": self.show_help,
            "new_chat": self.clear_conversation,
        }
        handler = handlers.get(str(action.get("value", "")))
        if handler:
            handler()

    def _render_quick_actions(self) -> None:
        for child in self.quick_grid.winfo_children():
            child.destroy()
        for index, action in enumerate(self.quick_action_items):
            self._quick_action_tile(
                self.quick_grid,
                (
                    str(action["icon"])
                    if self.has_fluent_icons
                    else FALLBACK_ACTION_ICONS.get(str(action["id"]).split(":", 1)[0], "✦")
                ),
                str(action["label"]),
                lambda item=action: self._execute_quick_action(item),
                row=index // 2,
                column=index % 2,
            )
        self.quick_grid.update_idletasks()
        self.quick_canvas.configure(scrollregion=self.quick_canvas.bbox("all"))
        self.quick_canvas.yview_moveto(0.0)

    def show_quick_action_setup(self) -> None:
        """Open the persistent quick-action layout editor."""

        c = self.colors
        working = [dict(action) for action in self.quick_action_items]
        dialog = tk.Toplevel(self.root)
        dialog.title("ACCESS — Quick Action Setup")
        dialog.geometry("650x540")
        dialog.minsize(590, 480)
        dialog.configure(bg=c["bg"])
        dialog.transient(self.root)
        dialog.grab_set()

        header = tk.Frame(dialog, bg=c["bg"])
        header.pack(fill="x", padx=26, pady=(24, 16))
        tk.Label(
            header,
            text="Set up quick actions",
            bg=c["bg"],
            fg=c["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Choose what appears in the sidebar and arrange it your way.",
            bg=c["bg"],
            fg=c["muted"],
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        content = tk.Frame(dialog, bg=c["bg"])
        content.pack(fill="both", expand=True, padx=26)
        list_shell = tk.Frame(
            content,
            bg=c["surface"],
            highlightthickness=1,
            highlightbackground=c["border"],
        )
        list_shell.pack(side="left", fill="both", expand=True)
        action_list = tk.Listbox(
            list_shell,
            relief="flat",
            bd=0,
            activestyle="none",
            selectmode="browse",
            bg=c["surface"],
            fg=c["text"],
            selectbackground=c["blue"],
            selectforeground="#FFFFFF",
            highlightthickness=0,
            font=("Segoe UI", 10),
        )
        list_scroll = ttk.Scrollbar(
            list_shell,
            orient="vertical",
            command=action_list.yview,
            style="Access.Vertical.TScrollbar",
        )
        action_list.configure(yscrollcommand=list_scroll.set)
        list_scroll.pack(side="right", fill="y")
        action_list.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        controls = tk.Frame(content, width=160, bg=c["bg"])
        controls.pack(side="left", fill="y", padx=(14, 0))
        controls.pack_propagate(False)

        def refresh(selected: int | None = None) -> None:
            action_list.delete(0, "end")
            for index, action in enumerate(working, start=1):
                suffix = "  • custom" if str(action["id"]).startswith("custom:") else ""
                action_list.insert("end", f"{index:02d}   {action['label']}{suffix}")
            if working:
                target = min(selected if selected is not None else 0, len(working) - 1)
                action_list.selection_set(target)
                action_list.activate(target)
                action_list.see(target)

        def selected_index() -> int | None:
            selection = action_list.curselection()
            return int(selection[0]) if selection else None

        def move(offset: int) -> None:
            index = selected_index()
            if index is None:
                return
            target = index + offset
            if not 0 <= target < len(working):
                return
            working[index], working[target] = working[target], working[index]
            refresh(target)

        def remove() -> None:
            index = selected_index()
            if index is not None:
                working.pop(index)
                refresh(max(0, index - 1))
                refresh_available()

        available_by_label: dict[str, str] = {}
        add_value = tk.StringVar()
        add_combo = ttk.Combobox(controls, textvariable=add_value, state="readonly", width=18)

        def refresh_available() -> None:
            used = {str(action["id"]) for action in working}
            available_by_label.clear()
            for action_id, action in QUICK_ACTION_CATALOG.items():
                if action_id not in used:
                    available_by_label[str(action["label"])] = action_id
            values = sorted(available_by_label)
            add_combo.configure(values=values)
            add_value.set(values[0] if values else "")

        def add_builtin() -> None:
            action_id = available_by_label.get(add_value.get())
            action = self._catalog_action(action_id or "")
            if action and len(working) < 24:
                working.append(action)
                refresh(len(working) - 1)
                refresh_available()

        def add_custom() -> None:
            if len(working) >= 24:
                messagebox.showinfo("Quick actions", "You can add up to 24 actions.", parent=dialog)
                return
            label = simpledialog.askstring(
                "Custom action",
                "Button label:",
                parent=dialog,
            )
            if not label or not label.strip():
                return
            command = simpledialog.askstring(
                "Custom action",
                "Command ACCESS should run:",
                parent=dialog,
            )
            if not command or not command.strip():
                return
            working.append(
                {
                    "id": f"custom:{uuid.uuid4().hex}",
                    "icon": "\ue945",
                    "label": label.strip()[:18],
                    "kind": "command",
                    "value": command.strip()[:500],
                }
            )
            refresh(len(working) - 1)

        def setup_button(text: str, command: Callable, accent: bool = False) -> tk.Button:
            return tk.Button(
                controls,
                text=text,
                command=command,
                relief="flat",
                bd=0,
                padx=10,
                pady=8,
                bg=c["accent"] if accent else c["surface"],
                activebackground=c["accent_hover"] if accent else c["surface_2"],
                fg="#06110F" if accent else c["text"],
                activeforeground="#06110F" if accent else c["text"],
                font=("Segoe UI", 9, "bold"),
                cursor="hand2",
            )

        setup_button("Move up", lambda: move(-1)).pack(fill="x", pady=(0, 5))
        setup_button("Move down", lambda: move(1)).pack(fill="x", pady=5)
        setup_button("Remove", remove).pack(fill="x", pady=5)
        tk.Frame(controls, height=1, bg=c["border"]).pack(fill="x", pady=12)
        tk.Label(controls, text="ADD BUILT-IN", bg=c["bg"], fg=c["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 5))
        add_combo.pack(fill="x", pady=(0, 5))
        setup_button("Add selected", add_builtin).pack(fill="x", pady=5)
        setup_button("Add custom…", add_custom).pack(fill="x", pady=5)

        footer = tk.Frame(dialog, bg=c["bg"])
        footer.pack(fill="x", padx=26, pady=20)

        def reset() -> None:
            working[:] = self._default_quick_actions()
            refresh()
            refresh_available()

        def save() -> None:
            if self._save_quick_actions(working):
                self.quick_action_items = [dict(action) for action in working]
                self._render_quick_actions()
                dialog.destroy()

        setup_button_reset = tk.Button(
            footer,
            text="Reset defaults",
            command=reset,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            bg=c["surface"],
            activebackground=c["surface_2"],
            fg=c["muted"],
            activeforeground=c["text"],
            font=("Segoe UI", 9),
            cursor="hand2",
        )
        setup_button_reset.pack(side="left")
        save_button = tk.Button(
            footer,
            text="Save layout",
            command=save,
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            bg=c["accent"],
            activebackground=c["accent_hover"],
            fg="#06110F",
            activeforeground="#06110F",
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        save_button.pack(side="right")
        tk.Button(
            footer,
            text="Cancel",
            command=dialog.destroy,
            relief="flat",
            bd=0,
            padx=14,
            pady=8,
            bg=c["bg"],
            activebackground=c["surface_2"],
            fg=c["muted"],
            activeforeground=c["text"],
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="right", padx=8)

        refresh()
        refresh_available()
        action_list.focus_set()

    def _quick_action_tile(
        self,
        parent: tk.Widget,
        icon: str,
        label: str,
        command: Callable,
        row: int,
        column: int,
    ) -> None:
        """Create a compact Fluent-icon launcher tile."""

        c = self.colors
        tile = tk.Frame(
            parent,
            height=53,
            bg=c["surface"],
            highlightthickness=1,
            highlightbackground=c["border"],
            cursor="hand2",
        )
        tile.grid(row=row, column=column, sticky="ew", padx=3, pady=3)
        tile.grid_propagate(False)
        icon_label = tk.Label(
            tile,
            text=icon,
            bg=c["surface"],
            fg=c["accent"],
            font=(self.icon_font_family, 17),
            cursor="hand2",
        )
        icon_label.pack(anchor="center", pady=(6, 0))
        text_label = tk.Label(
            tile,
            text=label,
            justify="center",
            anchor="center",
            wraplength=120,
            bg=c["surface"],
            fg=c["text"],
            font=("Segoe UI", 9, "bold"),
            cursor="hand2",
        )
        text_label.pack(fill="x", expand=True, padx=3, pady=(1, 6))

        widgets = (tile, icon_label, text_label)

        def set_hover(active: bool) -> None:
            background = c["surface_2"] if active else c["surface"]
            tile.configure(
                bg=background,
                highlightbackground=c["accent"] if active else c["border"],
            )
            icon_label.configure(bg=background)
            text_label.configure(bg=background)

        for widget in widgets:
            widget.bind("<Button-1>", lambda _event, callback=command: callback())
            widget.bind("<Enter>", lambda _event: set_hover(True))
            widget.bind("<Leave>", lambda _event: set_hover(False))
            widget.bind("<MouseWheel>", self._on_quick_mousewheel)
            widget.bind("<Button-4>", self._on_quick_mousewheel)
            widget.bind("<Button-5>", self._on_quick_mousewheel)

    def _create_app_icon(self) -> tk.PhotoImage:
        """Create the ACCESS mark for the title bar and Windows task switcher."""

        image = tk.PhotoImage(width=32, height=32)
        image.put("#20D3C2", to=(2, 2, 30, 30))
        ink = "#07101A"
        image.put(ink, to=(9, 21, 13, 27))
        image.put(ink, to=(19, 21, 23, 27))
        image.put(ink, to=(11, 13, 15, 22))
        image.put(ink, to=(17, 13, 21, 22))
        image.put(ink, to=(14, 8, 18, 13))
        image.put(ink, to=(13, 18, 20, 21))
        return image

    def _build_main(self) -> None:
        c = self.colors
        self.main = tk.Frame(self.shell, bg=c["bg"])
        self.main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.main, bg=c["bg"], height=98)
        header.pack(fill="x", padx=40, pady=(22, 0))
        header.pack_propagate(False)
        title_box = tk.Frame(header, bg=c["bg"])
        title_box.pack(side="left", fill="y", pady=(6, 0))
        tk.Label(
            title_box,
            text="Good to see you.",
            bg=c["bg"],
            fg=c["text"],
            font=("Segoe UI", 25, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="What can ACCESS help you accomplish?",
            bg=c["bg"],
            fg=c["muted"],
            font=("Segoe UI", 12),
        ).pack(anchor="w", pady=(8, 0))

        status_panel = RoundedPanel(
            header,
            c["surface"],
            c["border"],
            radius=14,
            width=166,
            height=48,
        )
        status_panel.pack(side="right", pady=(5, 0))
        status = status_panel.body
        tk.Label(status, text="●", bg=c["surface"], fg=c["success"], font=("Segoe UI", 11)).pack(side="left", padx=(18, 9), pady=12)
        tk.Label(status, text="System Online", bg=c["surface"], fg=c["text"], font=("Segoe UI", 10)).pack(side="left", padx=(0, 16))

        cards = tk.Frame(self.main, bg=c["bg"])
        cards.pack(fill="x", padx=40, pady=(0, 22))
        self._status_card(cards, "\ue950", "ENGINE", "Ready", c["accent"])
        self._status_card(cards, "\ue701", "MODE", "Offline-first", c["accent"])
        system_name = platform.system() or os.name
        platform_icon = "\ue782" if system_name == "Windows" else ("\ue711" if system_name == "Darwin" else "\ue7f8")
        self._status_card(cards, platform_icon, "PLATFORM", system_name, c["blue"])

        chat_panel = RoundedPanel(self.main, c["surface"], c["border"], radius=15)
        chat_panel.pack(fill="both", expand=True, padx=40, pady=(0, 20))
        chat_outer = chat_panel.body
        chat_title = tk.Frame(chat_outer, bg=c["surface"])
        chat_title.pack(fill="x", padx=24, pady=(14, 7))
        tk.Label(chat_title, text="Conversation", bg=c["surface"], fg=c["text"], font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(chat_title, text="⋮", bg=c["surface"], fg=c["muted"], font=("Segoe UI", 18)).pack(side="right", padx=(16, 0))
        self.activity_label = tk.Label(chat_title, text="Ready", bg=c["surface"], fg=c["muted"], font=("Segoe UI", 10))
        self.activity_label.pack(side="right")

        chat_body = tk.Frame(chat_outer, bg=c["surface"])
        chat_body.pack(fill="both", expand=True, padx=(10, 8), pady=(0, 14))
        self.chat_canvas = tk.Canvas(chat_body, bg=c["surface"], bd=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_body, orient="vertical", command=self.chat_canvas.yview, style="Access.Vertical.TScrollbar")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        # Keep scrolling available while matching the reference's clean edge.
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_frame = tk.Frame(self.chat_canvas, bg=c["surface"])
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_frame.bind("<Configure>", self._update_scroll_region)
        self.chat_canvas.bind("<Configure>", self._resize_chat_frame)
        # Bind to the main toplevel, not globally. ``bind_all`` also receives
        # wheel events from child windows such as History and scrolls the chat
        # behind them.
        self.root.bind("<MouseWheel>", self._on_mousewheel)
        self.root.bind("<Button-4>", self._on_mousewheel)
        self.root.bind("<Button-5>", self._on_mousewheel)

        self.confirmation_bar = tk.Frame(self.main, bg=c["surface_2"], highlightthickness=1, highlightbackground=c["danger"])
        self.confirmation_text = tk.Label(self.confirmation_bar, text="", bg=c["surface_2"], fg=c["text"], font=("Segoe UI", 9, "bold"))
        self.confirmation_text.pack(side="left", padx=14, pady=10)
        self._small_button(self.confirmation_bar, "Cancel", lambda: self.submit_command("no"), c["surface"]).pack(side="right", padx=(4, 12), pady=7)
        self._small_button(self.confirmation_bar, "Confirm", lambda: self.submit_command("yes"), c["danger"]).pack(side="right", padx=4, pady=7)

        composer_panel = RoundedPanel(
            self.main,
            c["input"],
            c["border"],
            radius=15,
            height=80,
        )
        composer_panel.pack(fill="x", padx=40, pady=(0, 40))
        composer = composer_panel.body
        self.command_entry = tk.Entry(
            composer,
            relief="flat",
            bd=0,
            bg=c["input"],
            fg=c["text"],
            insertbackground=c["accent"],
            font=("Segoe UI", 12),
        )
        self.command_entry.pack(side="left", fill="both", expand=True, padx=26, pady=22)
        self.command_entry.insert(0, "Type your message...")
        self.command_entry.configure(fg=c["muted"])
        self.command_entry.bind("<FocusIn>", self._clear_placeholder)
        self.command_entry.bind("<FocusOut>", self._restore_placeholder)
        self.send_button = tk.Button(
            composer,
            text="Send  →",
            command=self.submit_from_entry,
            relief="flat",
            bd=0,
            padx=28,
            pady=14,
            bg=c["accent"],
            activebackground=c["accent_hover"],
            fg="#06110F",
            activeforeground="#06110F",
            font=("Segoe UI", 12, "bold"),
            cursor="hand2",
        )
        self.send_button.pack(side="right", padx=18, pady=14)

    def _status_card(self, parent: tk.Widget, icon: str, label: str, value: str, color: str) -> None:
        c = self.colors
        panel = RoundedPanel(parent, c["surface"], c["border"], radius=14, height=84)
        panel.pack(side="left", fill="x", expand=True, padx=(0, 14))
        card = panel.body
        tk.Frame(card, width=4, bg=color).pack(side="left", fill="y")
        shown_icon = icon if self.has_fluent_icons else FALLBACK_ACTION_ICONS.get(label.casefold(), "◉")
        if label == "PLATFORM" and value == "Windows":
            logo = tk.Canvas(card, width=52, height=44, bg=c["surface"], bd=0, highlightthickness=0)
            logo.create_rectangle(8, 5, 25, 20, fill=color, outline=color)
            logo.create_rectangle(28, 5, 45, 20, fill=color, outline=color)
            logo.create_rectangle(8, 23, 25, 38, fill=color, outline=color)
            logo.create_rectangle(28, 23, 45, 38, fill=color, outline=color)
            logo.pack(side="left", padx=(18, 10))
        else:
            tk.Label(
                card,
                text=shown_icon,
                width=3,
                bg=c["surface"],
                fg=color,
                font=(self.icon_font_family, 24),
            ).pack(side="left", padx=(18, 10))
        body = tk.Frame(card, bg=c["surface"])
        body.pack(side="left", pady=15)
        tk.Label(body, text=label, bg=c["surface"], fg=c["muted"], font=("Segoe UI", 9)).pack(anchor="w")
        tk.Label(body, text=value, bg=c["surface"], fg=c["text"], font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(5, 0))

    def _small_button(self, parent: tk.Widget, text: str, command: Callable, bg: str) -> tk.Button:
        return tk.Button(parent, text=text, command=command, relief="flat", bd=0, padx=12, pady=5, bg=bg, activebackground=bg, fg=self.colors["text"], activeforeground=self.colors["text"], font=("Segoe UI", 9, "bold"), cursor="hand2")

    # --------------------------------------------------------------- interaction
    def _bind_shortcuts(self) -> None:
        self.root.bind("<Return>", lambda _event: self.submit_from_entry())
        self.root.bind("<Control-l>", lambda _event: self.command_entry.focus_set())
        self.root.bind("<Control-k>", lambda _event: self.command_entry.focus_set())
        self.root.bind("<Control-n>", lambda _event: self.clear_conversation())
        self.root.bind("<F1>", lambda _event: self.show_help())
        self.root.bind("<Escape>", lambda _event: self.command_entry.focus_set())

    def submit_from_entry(self) -> None:
        command = self.command_entry.get().strip()
        if command == "Type your message...":
            return
        self.command_entry.delete(0, "end")
        self.submit_command(command)

    def submit_command(self, command: str) -> None:
        command = (command or "").strip()
        if not command or self.busy:
            return

        command_lower = command.casefold()
        if command_lower in {"clear", "/clear", "clear chat", "new chat", "new conversation"}:
            self.clear_conversation()
            return
        if command_lower in {"help", "/help", "?", "/?", "commands", "show commands"}:
            self.show_help()
            return
        if command_lower in {"history", "/history", "show history"}:
            self.show_history()
            return
        if command_lower == "status":
            self._add_message(command, sender="user")
            self._add_message(
                f"System online. Engine ready in offline-first mode on {platform.system() or os.name}.",
                sender="assistant",
            )
            return
        if command_lower == "about":
            messagebox.showinfo(
                "About ACCESS",
                f"{APP_NAME} v{VERSION}\n\n{APP_SUBTITLE}\n\nOffline-first • Privacy-focused • Cross-platform",
                parent=self.root,
            )
            return

        self._hide_confirmation()
        self._add_message(command, sender="user")
        self._set_busy(True)
        threading.Thread(target=self._process_command, args=(command,), daemon=True).start()

    def _process_command(self, command: str) -> None:
        try:
            response = self.engine.process(command)
        except Exception as error:  # UI must remain usable after an engine error.
            response = f"I couldn't complete that command: {error}"
        self._results.put((command, response))

    def _poll_results(self) -> None:
        """Move worker results onto tkinter's main thread."""
        try:
            while True:
                command, response = self._results.get_nowait()
                self._complete_command(response, context=command)
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(50, self._poll_results)

    def _complete_command(self, response: str, context: str = "") -> None:
        self._add_message(response, sender="assistant", context=context)
        self._set_busy(False)
        if self.engine.pending_action:
            action = str(self.engine.pending_action).replace("_", " ").title()
            self.confirmation_text.configure(text=f"Confirmation required: {action}")
            self.confirmation_bar.pack(fill="x", padx=32, pady=(0, 10), before=self.command_entry.master)
        if not self.engine.running:
            self.root.after(700, self.close)
        self.command_entry.focus_set()

    def _set_busy(self, busy: bool) -> None:
        self.busy = busy
        self.activity_label.configure(text="ACCESS is thinking…" if busy else "Ready", fg=self.colors["accent"] if busy else self.colors["muted"])
        self.send_button.configure(state="disabled" if busy else "normal")
        self.command_entry.configure(state="disabled" if busy else "normal")

    def _add_welcome_message(self) -> None:
        self._add_message(
            "Hello! I'm ACCESS, your offline-first desktop assistant. I can open apps, control system settings, manage files, take screenshots, and remember our recent commands. How can I help?",
            sender="assistant",
        )

    def _add_message(self, text: str, sender: str, context: str = "") -> None:
        c = self.colors
        row = tk.Frame(self.chat_frame, bg=c["surface"])
        row.pack(fill="x", padx=6, pady=9)
        self._chat_rows.append(row)
        is_user = sender == "user"
        bubble_bg = c["user"] if is_user else c["surface_2"]
        if is_user:
            avatar = self._message_avatar(row, "U", c["blue"])
            avatar.pack(side="right", padx=(10, 4), anchor="n")
        else:
            avatar = self._message_avatar(row, "A", c["accent"])
            avatar.pack(side="left", padx=(2, 14), anchor="n")
        bubble = tk.Frame(
            row,
            bg=bubble_bg,
            padx=20,
            pady=14,
            highlightthickness=1,
            highlightbackground=c["border"] if not is_user else c["user"],
        )
        bubble.pack(
            side="right" if is_user else "left",
            padx=(160, 0) if is_user else (0, 160),
        )
        tk.Label(
            bubble,
            text="YOU" if is_user else "ACCESS",
            bg=bubble["bg"],
            fg="#DCE8FF" if is_user else c["accent"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        screenshot_path = None if is_user else self._screenshot_path(str(text), context)
        highlighted = None if is_user or screenshot_path else highlight_code(str(text), context)
        if screenshot_path:
            tk.Label(
                bubble,
                text="Screenshot captured",
                justify="left",
                anchor="w",
                bg=bubble["bg"],
                fg=c["text"],
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(5, 0))
            self._create_screenshot_attachment(bubble, screenshot_path)
        elif highlighted:
            self._create_code_widget(bubble, highlighted)
        else:
            label = tk.Label(
                bubble,
                text=str(text),
                justify="left",
                anchor="w",
                wraplength=690 if self.theme_name == "light" else 480,
                bg=bubble["bg"],
                fg="#FFFFFF" if is_user else c["text"],
                font=("Segoe UI", 12),
            )
            label.pack(anchor="w", pady=(8, 0))
        tk.Label(
            bubble,
            text=datetime.now().strftime("%H:%M"),
            bg=bubble["bg"],
            fg="#C6D4F3" if is_user else c["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="e", pady=(8, 0))
        self.root.after_idle(self._scroll_to_bottom)

    def _message_avatar(self, parent: tk.Widget, letter: str, color: str) -> tk.Canvas:
        canvas = tk.Canvas(parent, width=46, height=46, bg=self.colors["surface"], bd=0, highlightthickness=0)
        canvas.create_oval(2, 2, 44, 44, fill=color, outline=color)
        canvas.create_text(23, 23, text=letter, fill="#FFFFFF", font=("Segoe UI", 16, "bold"))
        return canvas

    @staticmethod
    def _screenshot_path(response: str, context: str = "") -> Path | None:
        marker = "Screenshot saved to:"
        if marker.casefold() not in response.casefold():
            return None
        start = response.casefold().find(marker.casefold()) + len(marker)
        value = response[start:].strip().strip("\"'")
        if not value:
            return None
        path = Path(value)
        if path.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
            return None
        return path

    def _create_screenshot_attachment(self, parent: tk.Widget, path: Path) -> None:
        c = self.colors
        card = tk.Frame(
            parent,
            bg=c["code_bg"],
            highlightthickness=1,
            highlightbackground=c["border"],
        )
        card.pack(anchor="w", fill="x", pady=(8, 2))

        loaded = False
        dimensions = ""
        try:
            from PIL import Image, ImageTk

            with Image.open(path) as source:
                original_width, original_height = source.size
                preview = source.copy()
            available_width = max(300, min(520, self.chat_canvas.winfo_width() - 220))
            resampling = getattr(Image, "Resampling", Image)
            preview.thumbnail((available_width, 290), resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
            dimensions = f"{original_width} × {original_height}  •  {path.suffix.lstrip('.').upper()}"
            loaded = True
        except (ImportError, OSError, ValueError):
            try:
                photo = tk.PhotoImage(file=str(path))
                scale = max(1, photo.width() // 500, photo.height() // 290)
                if scale > 1:
                    photo = photo.subsample(scale, scale)
                dimensions = f"{photo.width()} × {photo.height()}  •  {path.suffix.lstrip('.').upper()}"
                loaded = True
            except (tk.TclError, OSError):
                loaded = False

        if loaded:
            self._image_refs.append(photo)
            preview_label = tk.Label(
                card,
                image=photo,
                bg=c["code_bg"],
                bd=0,
                cursor="hand2",
            )
            preview_label.pack(fill="x", padx=8, pady=(8, 5))
            preview_label.bind("<Button-1>", lambda _event: self._open_file(path))
        else:
            tk.Label(
                card,
                text="Preview unavailable",
                bg=c["code_bg"],
                fg=c["muted"],
                font=("Segoe UI", 9),
            ).pack(fill="x", padx=14, pady=18)

        details = tk.Frame(card, bg=c["code_bg"])
        details.pack(fill="x", padx=10, pady=(2, 8))
        text_box = tk.Frame(details, bg=c["code_bg"])
        text_box.pack(side="left", fill="x", expand=True)
        tk.Label(
            text_box,
            text=path.name,
            anchor="w",
            bg=c["code_bg"],
            fg=c["text"],
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            text_box,
            text=dimensions or str(path.parent),
            anchor="w",
            bg=c["code_bg"],
            fg=c["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(2, 0))

        actions = tk.Frame(card, bg=c["code_bg"])
        actions.pack(fill="x", padx=10, pady=(0, 10))
        self._attachment_button(actions, "Open image", lambda: self._open_file(path), primary=True).pack(side="left")
        self._attachment_button(actions, "Show in folder", lambda: self._show_file(path)).pack(side="left", padx=6)
        self._attachment_button(actions, "Copy path", lambda: self._copy_path(path)).pack(side="left")

    def _attachment_button(
        self,
        parent: tk.Widget,
        text: str,
        command: Callable,
        primary: bool = False,
    ) -> tk.Button:
        c = self.colors
        return tk.Button(
            parent,
            text=text,
            command=command,
            relief="flat",
            bd=0,
            padx=10,
            pady=6,
            bg=c["accent"] if primary else c["surface_2"],
            activebackground=c["accent_hover"] if primary else c["surface"],
            fg="#06110F" if primary else c["text"],
            activeforeground="#06110F" if primary else c["text"],
            font=("Segoe UI", 8, "bold"),
            cursor="hand2",
        )

    def _open_file(self, path: Path) -> None:
        try:
            if not path.is_file():
                raise FileNotFoundError(path)
            if platform.system() == "Windows":
                os.startfile(str(path))
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except (OSError, FileNotFoundError) as error:
            messagebox.showerror("Unable to open screenshot", str(error), parent=self.root)

    def _show_file(self, path: Path) -> None:
        try:
            if not path.exists():
                raise FileNotFoundError(path)
            if platform.system() == "Windows":
                subprocess.Popen(["explorer.exe", "/select,", str(path)])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", "-R", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path.parent)])
        except (OSError, FileNotFoundError) as error:
            messagebox.showerror("Unable to show screenshot", str(error), parent=self.root)

    def _copy_path(self, path: Path) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(str(path))
        self.root.update_idletasks()

    def _configure_syntax_tags(self, widget: tk.Text, prefix: str = "", block: bool = False) -> None:
        c = self.colors
        base = {
            "code": c["code_text"],
            "comment": c["code_comment"],
            "keyword": c["code_keyword"],
            "string": c["code_string"],
            "number": c["code_number"],
            "function": c["code_function"],
            "type": c["code_type"],
            "operator": c["code_text"],
            "preprocessor": c["code_preprocessor"],
        }
        for name, color in base.items():
            options = {
                "foreground": color,
                "font": ("Consolas", 10),
            }
            if block:
                options.update(
                    background=c["code_bg"],
                    lmargin1=12,
                    lmargin2=12,
                    rmargin=12,
                )
            widget.tag_configure(f"{prefix}{name}", **options)

    def _insert_highlighted(self, widget: tk.Text, highlighted: HighlightedCode, prefix: str = "") -> None:
        for piece, token_name in highlighted.segments:
            widget.insert("end", piece, f"{prefix}{token_name}")

    def _create_code_widget(self, parent: tk.Widget, highlighted: HighlightedCode) -> None:
        c = self.colors
        code_shell = tk.Frame(
            parent,
            bg=c["code_bg"],
            highlightthickness=1,
            highlightbackground=c["border"],
        )
        code_shell.pack(anchor="w", fill="x", pady=(7, 0))
        tk.Label(
            code_shell,
            text=highlighted.language.upper(),
            bg=c["code_bg"],
            fg=c["muted"],
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(8, 3))

        lines = highlighted.code.splitlines() or [""]
        visible_lines = min(max(len(lines), 2), 20)
        width = min(max(max((len(line) for line in lines), default=0) + 2, 48), 86)
        text_frame = tk.Frame(code_shell, bg=c["code_bg"])
        text_frame.pack(fill="both", expand=True, padx=(8, 4), pady=(0, 8))
        code_view = tk.Text(
            text_frame,
            width=width,
            height=visible_lines,
            wrap="none",
            relief="flat",
            bd=0,
            padx=6,
            pady=5,
            bg=c["code_bg"],
            fg=c["code_text"],
            insertbackground=c["accent"],
            selectbackground=c["blue"],
            font=("Consolas", 10),
        )
        code_view.pack(side="left", fill="both", expand=True)
        self._configure_syntax_tags(code_view)
        self._insert_highlighted(code_view, highlighted)
        code_view.configure(state="disabled")

        if len(lines) > 20:
            scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=code_view.yview)
            scrollbar.pack(side="right", fill="y")
            code_view.configure(yscrollcommand=scrollbar.set)
        if any(len(line) > 86 for line in lines):
            horizontal = ttk.Scrollbar(code_shell, orient="horizontal", command=code_view.xview)
            horizontal.pack(fill="x", padx=8, pady=(0, 5))
            code_view.configure(xscrollcommand=horizontal.set)

        # Let a code block consume the wheel only when it has its own scroll area.
        if len(lines) > 20:
            def scroll_code(event) -> str:
                code_view.yview_scroll(self._wheel_units(event), "units")
                return "break"

            code_view.bind("<MouseWheel>", scroll_code)
            code_view.bind("<Button-4>", scroll_code)
            code_view.bind("<Button-5>", scroll_code)

    # ----------------------------------------------------------------- dialogs
    def show_history(self) -> None:
        c = self.colors
        dialog = tk.Toplevel(self.root)
        dialog.title("ACCESS — History")
        dialog.geometry("760x560")
        dialog.minsize(600, 420)
        dialog.configure(bg=c["bg"])
        dialog.transient(self.root)

        header = tk.Frame(dialog, bg=c["bg"])
        header.pack(fill="x", padx=24, pady=(22, 14))
        tk.Label(header, text="Conversation history", bg=c["bg"], fg=c["text"], font=("Segoe UI", 18, "bold")).pack(anchor="w")
        tk.Label(header, text="Stored locally on this device", bg=c["bg"], fg=c["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

        search_frame = tk.Frame(dialog, bg=c["input"], highlightthickness=1, highlightbackground=c["border"])
        search_frame.pack(fill="x", padx=24, pady=(0, 14))
        search_var = tk.StringVar()
        entry = tk.Entry(search_frame, textvariable=search_var, relief="flat", bd=0, bg=c["input"], fg=c["text"], insertbackground=c["accent"], font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True, padx=12, pady=11)

        list_frame = tk.Frame(dialog, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        list_frame.pack(fill="both", expand=True, padx=24, pady=(0, 24))
        history_scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            style="Access.Vertical.TScrollbar",
        )
        history_scrollbar.pack(side="right", fill="y")
        history = tk.Text(
            list_frame,
            wrap="word",
            relief="flat",
            bd=0,
            padx=16,
            pady=14,
            bg=c["surface"],
            fg=c["text"],
            insertbackground=c["accent"],
            font=("Segoe UI", 10),
            state="disabled",
            yscrollcommand=history_scrollbar.set,
        )
        history.pack(side="left", fill="both", expand=True)
        history_scrollbar.configure(command=history.yview)
        history.tag_configure("time", foreground=c["muted"], font=("Segoe UI", 8))
        history.tag_configure("user", foreground=c["blue"], font=("Segoe UI", 10, "bold"))
        history.tag_configure("assistant", foreground=c["text"], spacing3=14)
        history.tag_configure("assistant_header", foreground=c["accent"], font=("Segoe UI", 9, "bold"))
        history.tag_configure("language", foreground=c["muted"], background=c["code_bg"], font=("Segoe UI", 8, "bold"), lmargin1=12, lmargin2=12)
        self._configure_syntax_tags(history, prefix="syntax_", block=True)

        def load(*_args) -> None:
            query = search_var.get().strip()
            rows = self.engine.search_memory(query, 100) if query else self.engine.get_recent_memory(100)
            history.configure(state="normal")
            history.delete("1.0", "end")
            if not rows:
                history.insert("end", "No matching conversations yet.", "time")
            for row_index, (user_input, response, created_at) in enumerate(rows):
                stamp = created_at.replace("T", " ") if created_at else ""
                history.insert("end", f"{stamp}\n", "time")
                history.insert("end", f"You: {user_input}\n", "user")
                screenshot_path = self._screenshot_path(response, user_input)
                highlighted = None if screenshot_path else highlight_code(response, user_input)
                if screenshot_path:
                    link_tag = f"screenshot_link_{row_index}"
                    history.insert("end", "ACCESS: Screenshot captured\n", "assistant_header")
                    history.insert("end", f"Open {screenshot_path.name}\n\n", link_tag)
                    history.tag_configure(
                        link_tag,
                        foreground=c["blue"] if screenshot_path.exists() else c["muted"],
                        underline=True,
                        font=("Segoe UI", 10, "bold"),
                    )
                    history.tag_bind(
                        link_tag,
                        "<Button-1>",
                        lambda _event, path=screenshot_path: self._open_file(path),
                    )
                    history.tag_bind(link_tag, "<Enter>", lambda _event: history.configure(cursor="hand2"))
                    history.tag_bind(link_tag, "<Leave>", lambda _event: history.configure(cursor="xterm"))
                elif highlighted:
                    history.insert("end", "ACCESS\n", "assistant_header")
                    history.insert("end", f"  {highlighted.language.upper()}\n", "language")
                    self._insert_highlighted(history, highlighted, prefix="syntax_")
                    history.insert("end", "\n\n", "syntax_code")
                else:
                    history.insert("end", f"ACCESS: {response}\n\n", "assistant")
            history.configure(state="disabled")
            history.yview_moveto(0.0)

        search_var.trace_add("write", load)
        load()
        entry.focus_set()

    def show_help(self) -> None:
        commands = (
            "Try commands like:\n\n"
            "  open chrome  •  close calculator\n"
            "  volume up  •  mute  •  brightness down\n"
            "  take a screenshot  •  lock screen\n"
            "  create file notes.txt  •  read file notes.txt\n"
            "  search file report  •  copy file A to B\n"
            "  move file A to B  •  rename file A to B\n"
            "  shutdown  •  restart  •  sleep\n\n"
            "Shortcuts: Enter to send, Ctrl+K to focus, Ctrl+N for a new conversation, F1 for help."
        )
        messagebox.showinfo("ACCESS commands", commands, parent=self.root)

    # ---------------------------------------------------------------- utilities
    def clear_conversation(self) -> None:
        for row in self._chat_rows:
            row.destroy()
        self._chat_rows.clear()
        self._image_refs.clear()
        self._add_welcome_message()
        self.command_entry.focus_set()

    def toggle_theme(self) -> None:
        self.theme_name = "light" if self.theme_name == "dark" else "dark"
        # Rebuilding is safer than recursively recoloring widgets with mixed roles.
        self.app_container.destroy()
        self.colors = THEMES[self.theme_name]
        self.root.configure(bg=self.colors["bg"])
        self._chat_rows.clear()
        self._image_refs.clear()
        self._configure_styles()
        self._build_layout()
        self._add_welcome_message()
        self.command_entry.focus_set()

    def _hide_confirmation(self) -> None:
        if self.confirmation_bar.winfo_manager():
            self.confirmation_bar.pack_forget()

    def _clear_placeholder(self, _event=None) -> None:
        if self.command_entry.get() == "Type your message...":
            self.command_entry.delete(0, "end")
            self.command_entry.configure(fg=self.colors["text"])

    def _restore_placeholder(self, _event=None) -> None:
        if not self.command_entry.get():
            self.command_entry.insert(0, "Type your message...")
            self.command_entry.configure(fg=self.colors["muted"])

    def _update_scroll_region(self, _event=None) -> None:
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def _resize_chat_frame(self, event) -> None:
        self.chat_canvas.itemconfigure(self.chat_window, width=event.width)

    def _on_mousewheel(self, event) -> None:
        if not self.chat_canvas.winfo_exists():
            return
        pointer_widget = self.root.winfo_containing(
            self.root.winfo_pointerx(),
            self.root.winfo_pointery(),
        )
        widget = pointer_widget
        while widget is not None and widget is not self.chat_canvas:
            widget = getattr(widget, "master", None)
        if widget is self.chat_canvas:
            self.chat_canvas.yview_scroll(self._wheel_units(event), "units")

    def _on_quick_mousewheel(self, event) -> str:
        if self.quick_canvas.winfo_exists():
            self.quick_canvas.yview_scroll(self._wheel_units(event), "units")
        return "break"

    @staticmethod
    def _wheel_units(event) -> int:
        """Normalize Windows/macOS MouseWheel and Linux Button-4/5 events."""

        button_number = getattr(event, "num", None)
        if button_number == 4:
            return -3
        if button_number == 5:
            return 3
        delta = getattr(event, "delta", 0)
        if not delta:
            return 0
        # Windows normally reports ±120; macOS commonly reports small deltas.
        if abs(delta) < 120:
            return -1 if delta > 0 else 1
        return int(-delta / 120)

    def _scroll_to_bottom(self) -> None:
        self.chat_canvas.update_idletasks()
        self.chat_canvas.yview_moveto(1.0)

    def close(self) -> None:
        self.engine.running = False
        try:
            self.engine.memory.close()
        except Exception:
            pass
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def start_gui() -> None:
    """Launch the ACCESS desktop application."""
    AccessGUI().run()


if __name__ == "__main__":
    start_gui()
