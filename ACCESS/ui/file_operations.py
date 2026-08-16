"""The themed file-management workspace used by the ACCESS desktop UI."""

from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk
from typing import Callable


TEXT_EXTENSIONS = {
    ".cfg", ".conf", ".css", ".csv", ".env", ".html", ".ini", ".js",
    ".json", ".log", ".md", ".py", ".sh", ".sql", ".toml", ".tsv",
    ".txt", ".xml", ".yaml", ".yml",
}


def format_file_size(size: int) -> str:
    value = float(max(0, size))
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024 or unit == "TB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TB"


def reveal_command(path: Path, system: str | None = None) -> list[str]:
    """Build the native reveal/open-parent command for the current platform."""

    system = system or platform.system()
    if system == "Windows":
        return ["explorer", f"/select,{path}"]
    if system == "Darwin":
        return ["open", "-R", str(path)]
    return ["xdg-open", str(path if path.is_dir() else path.parent)]


def duplicate_destination(path: Path) -> Path:
    """Return a non-conflicting sibling name for a copied item."""

    stem, suffix = (path.stem, path.suffix) if path.is_file() else (path.name, "")
    candidate = path.with_name(f"{stem} copy{suffix}")
    number = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem} copy {number}{suffix}")
        number += 1
    return candidate


def is_hidden(path: Path) -> bool:
    """Recognize Unix dotfiles and the native Windows hidden attribute."""

    if path.name.startswith("."):
        return True
    if platform.system() == "Windows":
        try:
            attributes = path.stat().st_file_attributes
            return bool(attributes & stat.FILE_ATTRIBUTE_HIDDEN)
        except (AttributeError, OSError):
            return False
    return False


class FileOperationsWindow:
    """Browse and organize files with guarded destructive operations."""

    def __init__(self, parent: tk.Misc, colors: dict[str, str], *,
                 initial_directory: Path | None = None,
                 on_close: Callable[[], None] | None = None) -> None:
        self.colors, self.on_close = colors, on_close
        start = (initial_directory or Path.home()).expanduser()
        self.current_directory = start.resolve() if start.is_dir() else Path.home()
        self.history, self.history_index = [self.current_directory], 0
        self.sort_column, self.sort_reverse = "name", False
        self.items: dict[str, Path] = {}
        self.selected_path: Path | None = None
        self.window = tk.Toplevel(parent)
        self.window.title("ACCESS — File Operations")
        self.window.configure(bg=colors["bg"])
        self.window.minsize(920, 600)
        width = min(1220, self.window.winfo_screenwidth() - 80)
        height = min(760, self.window.winfo_screenheight() - 100)
        x, y = (self.window.winfo_screenwidth() - width) // 2, (self.window.winfo_screenheight() - height) // 2
        self.window.geometry(f"{width}x{height}+{max(0, x)}+{max(0, y)}")
        self.window.transient(parent)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.location_var = tk.StringVar(self.window, value=str(self.current_directory))
        self.search_var = tk.StringVar(self.window)
        self.hidden_var = tk.BooleanVar(self.window, value=False)
        self.status_var = tk.StringVar(self.window, value="Ready")
        self.detail_name = tk.StringVar(self.window, value="Select an item")
        self.detail_meta = tk.StringVar(
            self.window, value="Choose a file or folder to see details."
        )
        self._styles()
        self._build()
        self._bindings()
        self.refresh()

    def _styles(self) -> None:
        c, style = self.colors, ttk.Style(self.window)
        try: style.theme_use("clam")
        except tk.TclError: pass
        style.configure("Files.Treeview", background=c["surface"], fieldbackground=c["surface"], foreground=c["text"], rowheight=38, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Files.Treeview.Heading", background=c["surface_2"], foreground=c["muted"], relief="flat", padding=(9, 8), font=("Segoe UI", 9, "bold"))
        style.map("Files.Treeview", background=[("selected", c["user"])], foreground=[("selected", "#FFFFFF")])
        style.configure("Files.Vertical.TScrollbar", background=c["surface_2"], troughcolor=c["surface"], bordercolor=c["surface"], arrowcolor=c["muted"])

    def _button(self, parent: tk.Widget, text: str, command: Callable, *, primary=False, danger=False) -> tk.Button:
        c = self.colors
        bg, fg = (c["accent"], "#06110F") if primary else (c["surface_2"], c["danger"] if danger else c["text"])
        return tk.Button(parent, text=text, command=command, relief="flat", bd=0, padx=14, pady=9, bg=bg,
                         activebackground=c["danger"] if danger else (c["accent_hover"] if primary else c["border"]),
                         fg=fg, activeforeground="#FFFFFF" if danger else fg, font=("Segoe UI", 9, "bold"), cursor="hand2")

    def _build(self) -> None:
        c = self.colors
        header = tk.Frame(self.window, bg=c["bg"]); header.pack(fill="x", padx=28, pady=(24, 16))
        titles = tk.Frame(header, bg=c["bg"]); titles.pack(side="left")
        tk.Label(titles, text="File Operations", bg=c["bg"], fg=c["text"], font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(titles, text="Browse, preview, and organize your local files.", bg=c["bg"], fg=c["muted"], font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 0))
        self._button(header, "New folder", self.create_folder, primary=True).pack(side="right", padx=(8, 0))
        self._button(header, "New file", self.create_file).pack(side="right")
        nav = tk.Frame(self.window, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"]); nav.pack(fill="x", padx=28, pady=(0, 14))
        for text, callback in (("←", self.back), ("→", self.forward), ("↑", self.up), ("↻", self.refresh)):
            button = self._button(nav, text, callback); button.configure(width=3, padx=3, font=("Segoe UI Symbol", 12, "bold")); button.pack(side="left", padx=4, pady=9)
        self.location_entry = tk.Entry(nav, textvariable=self.location_var, relief="flat", bd=0, bg=c["input"], fg=c["text"], insertbackground=c["accent"], font=("Segoe UI", 10))
        self.location_entry.pack(side="left", fill="x", expand=True, padx=8, ipady=9); self.location_entry.bind("<Return>", lambda _e: self.go_location())
        search = tk.Frame(nav, bg=c["input"]); search.pack(side="right", padx=10, pady=9)
        tk.Label(search, text="⌕", bg=c["input"], fg=c["muted"], font=("Segoe UI Symbol", 14)).pack(side="left", padx=(10, 2))
        self.search_entry = tk.Entry(search, textvariable=self.search_var, width=22, relief="flat", bd=0, bg=c["input"], fg=c["text"], insertbackground=c["accent"], font=("Segoe UI", 10))
        self.search_entry.pack(side="left", padx=(0, 10), ipady=8); self.search_entry.bind("<KeyRelease>", lambda _e: self.refresh())
        body = tk.Frame(self.window, bg=c["bg"]); body.pack(fill="both", expand=True, padx=28); body.columnconfigure(1, weight=1); body.rowconfigure(0, weight=1)
        self._places(body); self._listing(body); self._details(body)
        footer = tk.Frame(self.window, bg=c["bg"]); footer.pack(fill="x", padx=30, pady=(12, 18))
        tk.Label(footer, textvariable=self.status_var, bg=c["bg"], fg=c["muted"], font=("Segoe UI", 9)).pack(side="left")
        tk.Checkbutton(footer, text="Show hidden items", variable=self.hidden_var, command=self.refresh, bg=c["bg"], activebackground=c["bg"], fg=c["muted"], activeforeground=c["text"], selectcolor=c["surface"], font=("Segoe UI", 9)).pack(side="right")

    def _places(self, parent: tk.Widget) -> None:
        c = self.colors
        panel = tk.Frame(parent, width=185, bg=c["sidebar"], highlightthickness=1, highlightbackground=c["border"]); panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12)); panel.grid_propagate(False)
        tk.Label(panel, text="PLACES", bg=c["sidebar"], fg=c["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(18, 10))
        home = Path.home()
        for icon, label, path in (("⌂", "Home", home), ("▣", "Desktop", home / "Desktop"), ("▤", "Documents", home / "Documents"), ("↓", "Downloads", home / "Downloads"), ("◆", "Project", Path.cwd())):
            if path.is_dir(): self._place(panel, icon, label, lambda p=path: self.navigate(p))
        tk.Frame(panel, height=1, bg=c["border"]).pack(fill="x", padx=16, pady=10)
        self._place(panel, "+", "Choose folder", self.choose_folder)

    def _place(self, parent: tk.Widget, icon: str, label: str, command: Callable) -> None:
        c = self.colors
        tk.Button(parent, text=f"{icon}   {label}", command=command, anchor="w", relief="flat", bd=0, padx=18, pady=10, bg=c["sidebar"], activebackground=c["surface_2"], fg=c["text"], activeforeground=c["text"], font=("Segoe UI", 10), cursor="hand2").pack(fill="x", padx=8, pady=1)

    def _listing(self, parent: tk.Widget) -> None:
        c = self.colors
        panel = tk.Frame(parent, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"]); panel.grid(row=0, column=1, sticky="nsew", padx=(0, 12)); panel.rowconfigure(1, weight=1); panel.columnconfigure(0, weight=1)
        heading = tk.Frame(panel, bg=c["surface"]); heading.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        self.folder_label = tk.Label(heading, bg=c["surface"], fg=c["text"], font=("Segoe UI", 13, "bold")); self.folder_label.pack(side="left")
        self.count_label = tk.Label(heading, bg=c["surface"], fg=c["muted"], font=("Segoe UI", 9)); self.count_label.pack(side="right")
        shell = tk.Frame(panel, bg=c["surface"]); shell.grid(row=1, column=0, sticky="nsew", padx=(10, 4), pady=(0, 10)); shell.rowconfigure(0, weight=1); shell.columnconfigure(0, weight=1)
        self.tree = ttk.Treeview(shell, columns=("type", "size", "modified"), show="tree headings", selectmode="browse", style="Files.Treeview")
        for column, label in (("#0", "NAME"), ("type", "TYPE"), ("size", "SIZE"), ("modified", "MODIFIED")):
            sort_key = "name" if column == "#0" else column
            self.tree.heading(column, text=label, command=lambda key=sort_key: self.sort_by(key))
        self.tree.column("#0", width=280, minwidth=180); self.tree.column("type", width=100, stretch=False); self.tree.column("size", width=85, anchor="e", stretch=False); self.tree.column("modified", width=140, stretch=False)
        scroll = ttk.Scrollbar(shell, orient="vertical", command=self.tree.yview, style="Files.Vertical.TScrollbar"); self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew"); scroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self.select); self.tree.bind("<Double-Button-1>", lambda _e: self.open_selected())

    def _details(self, parent: tk.Widget) -> None:
        c = self.colors
        panel = tk.Frame(parent, width=280, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"]); panel.grid(row=0, column=2, sticky="nsew"); panel.grid_propagate(False)
        self.detail_icon = tk.Label(panel, text="◇", bg=c["surface"], fg=c["accent"], font=("Segoe UI Symbol", 34, "bold")); self.detail_icon.pack(anchor="w", padx=20, pady=(22, 8))
        tk.Label(panel, textvariable=self.detail_name, wraplength=235, justify="left", bg=c["surface"], fg=c["text"], font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20)
        tk.Label(panel, textvariable=self.detail_meta, wraplength=235, justify="left", bg=c["surface"], fg=c["muted"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(7, 14))
        tk.Label(panel, text="PREVIEW", bg=c["surface"], fg=c["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=20)
        self.preview = tk.Text(panel, height=12, wrap="word", relief="flat", bd=0, padx=12, pady=10, bg=c["code_bg"], fg=c["code_text"], font=("Consolas", 9)); self.preview.pack(fill="both", expand=True, padx=20, pady=(6, 12)); self._preview("No preview selected.")
        actions = tk.Frame(panel, bg=c["surface"]); actions.pack(fill="x", padx=16, pady=(0, 16)); actions.columnconfigure(0, weight=1); actions.columnconfigure(1, weight=1)
        specs = (("Open", self.open_selected, 0, 0, True, False, 1), ("Rename", self.rename_selected, 0, 1, False, False, 1), ("Copy to", self.copy_selected, 1, 0, False, False, 1), ("Move to", self.move_selected, 1, 1, False, False, 1), ("Duplicate", self.duplicate_selected, 2, 0, False, False, 1), ("Copy path", self.copy_path, 2, 1, False, False, 1), ("Reveal", self.reveal_selected, 3, 0, False, False, 2), ("Move to Trash", self.delete_selected, 4, 0, False, True, 2))
        for text, cmd, row, col, primary, danger, span in specs: self._button(actions, text, cmd, primary=primary, danger=danger).grid(row=row, column=col, columnspan=span, sticky="ew", padx=4, pady=4)

    def _bindings(self) -> None:
        self.window.bind("<Alt-Left>", lambda _e: self.back()); self.window.bind("<Alt-Up>", lambda _e: self.up())
        self.window.bind("<Alt-Right>", lambda _e: self.forward())
        self.window.bind("<Control-l>", lambda _e: (self.location_entry.focus_set(), self.location_entry.select_range(0, "end")))
        self.window.bind("<Control-f>", lambda _e: self.search_entry.focus_set()); self.window.bind("<F5>", lambda _e: self.refresh())
        self.window.bind("<F2>", lambda _e: self.rename_selected()); self.window.bind("<Delete>", lambda _e: self.delete_selected())

    def refresh(self) -> None:
        self.tree.delete(*self.tree.get_children()); self.items.clear(); self.selected_path = None
        query = self.search_var.get().strip().casefold()
        try: paths = list(self.current_directory.iterdir())
        except OSError as error: self.status_var.set(f"Unable to read folder: {error}"); return
        paths = [p for p in paths if (self.hidden_var.get() or not is_hidden(p)) and (not query or query in p.name.casefold())]
        paths.sort(key=lambda p: (not p.is_dir(), p.name.casefold()))
        for path in paths:
            try:
                stat, folder = path.stat(), path.is_dir(); kind = "Folder" if folder else (path.suffix[1:].upper() or "File")
                values = (kind, "—" if folder else format_file_size(stat.st_size), datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %Y  %H:%M"))
            except OSError: folder, values = False, ("Unavailable", "—", "—")
            item = self.tree.insert("", "end", text=f"{'▸' if folder else '•'}  {path.name}", values=values); self.items[item] = path
        count = f"{len(paths)} item" + ("" if len(paths) == 1 else "s")
        self.folder_label.configure(text=self.current_directory.name or str(self.current_directory)); self.count_label.configure(text=count)
        self.status_var.set(f"{count}  •  {self.current_directory}"); self._empty_details()

    def sort_by(self, column: str) -> None:
        """Sort the visible list, toggling direction on repeated clicks."""

        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column, self.sort_reverse = column, False
        children = list(self.tree.get_children())
        def key(item: str):
            path = self.items[item]
            try:
                stat = path.stat()
            except OSError:
                stat = None
            if column == "name": return (not path.is_dir(), path.name.casefold())
            if column == "type": return (self.tree.set(item, "type").casefold(), path.name.casefold())
            if column == "size": return -1 if stat is None or path.is_dir() else stat.st_size
            return -1 if stat is None else stat.st_mtime
        for index, item in enumerate(sorted(children, key=key, reverse=self.sort_reverse)):
            self.tree.move(item, "", index)

    def select(self, _event=None) -> None:
        chosen = self.tree.selection()
        if not chosen: return
        path = self.items[chosen[0]]; self.selected_path = path; self.detail_icon.configure(text="▰" if path.is_dir() else "◇"); self.detail_name.set(path.name)
        try:
            stat = path.stat(); kind = "Folder" if path.is_dir() else (path.suffix[1:].upper() or "File"); size = "—" if path.is_dir() else format_file_size(stat.st_size)
            self.detail_meta.set(f"{kind}  •  {size}\nModified {datetime.fromtimestamp(stat.st_mtime):%B %d, %Y at %H:%M}")
            if path.is_dir(): self._preview(f"Folder containing {sum(1 for _ in path.iterdir())} item(s).\n\nDouble-click to browse.")
            elif path.suffix.casefold() in TEXT_EXTENSIONS or path.name == ".gitignore":
                if stat.st_size > 512_000: self._preview("This file is too large to preview safely.")
                else:
                    text = path.read_text(encoding="utf-8"); self._preview((text[:8000] + "\n\n… Preview truncated …") if len(text) > 8000 else (text or "(Empty file)"))
            else: self._preview("Preview is available for text and code files.\n\nOpen this item in its default application.")
        except (OSError, UnicodeDecodeError) as error: self._preview(f"Preview unavailable: {error}")

    def _preview(self, text: str) -> None:
        self.preview.configure(state="normal"); self.preview.delete("1.0", "end"); self.preview.insert("1.0", text); self.preview.configure(state="disabled")

    def _empty_details(self) -> None:
        self.selected_path = None; self.detail_icon.configure(text="◇"); self.detail_name.set("Select an item"); self.detail_meta.set("Choose a file or folder to see details."); self._preview("No preview selected.")

    def navigate(self, path: Path, *, record=True) -> None:
        try: path = path.expanduser().resolve()
        except OSError as error: self._error("open the folder", error); return
        if not path.is_dir(): messagebox.showerror("Folder not found", str(path), parent=self.window); return
        self.current_directory = path; self.location_var.set(str(path)); self.search_var.set("")
        if record and self.history[-1] != path: self.history = self.history[:self.history_index + 1] + [path]; self.history_index = len(self.history) - 1
        self.refresh()

    def back(self) -> None:
        if self.history_index > 0: self.history_index -= 1; self.navigate(self.history[self.history_index], record=False)
    def forward(self) -> None:
        if self.history_index < len(self.history) - 1: self.history_index += 1; self.navigate(self.history[self.history_index], record=False)
    def up(self) -> None:
        if self.current_directory.parent != self.current_directory: self.navigate(self.current_directory.parent)
    def go_location(self) -> None:
        self.navigate(Path(os.path.expandvars(self.location_var.get().strip().strip('"'))))
    def choose_folder(self) -> None:
        value = filedialog.askdirectory(initialdir=self.current_directory, parent=self.window)
        if value: self.navigate(Path(value))

    def _safe_name(self, title: str, prompt: str, initial: str = "") -> Path | None:
        name = simpledialog.askstring(title, prompt, initialvalue=initial, parent=self.window)
        if not name: return None
        name = name.strip()
        if Path(name).name != name or name in {".", ".."}: messagebox.showerror("Invalid name", "Enter a name without folder separators.", parent=self.window); return None
        return self.current_directory / name

    def create_file(self) -> None:
        path = self._safe_name("New file", "File name:")
        if path is None: return
        try: path.touch(exist_ok=False); self.refresh(); self.status_var.set(f"Created {path.name}")
        except OSError as error: self._error("create the file", error)
    def create_folder(self) -> None:
        path = self._safe_name("New folder", "Folder name:")
        if path is None: return
        try: path.mkdir(exist_ok=False); self.refresh(); self.status_var.set(f"Created {path.name}")
        except OSError as error: self._error("create the folder", error)

    def _selected(self) -> Path | None:
        if self.selected_path and self.selected_path.exists(): return self.selected_path
        messagebox.showinfo("Select an item", "Select a file or folder first.", parent=self.window); return None
    def open_selected(self) -> None:
        path = self._selected()
        if path is None: return
        if path.is_dir(): self.navigate(path); return
        try:
            if platform.system() == "Windows": os.startfile(path)  # type: ignore[attr-defined]
            else: subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", str(path)])
        except OSError as error: self._error("open the item", error)
    def rename_selected(self) -> None:
        source = self._selected()
        if source is None: return
        destination = self._safe_name("Rename item", "New name:", source.name)
        if destination is None or destination == source: return
        if destination.exists(): messagebox.showwarning("Name already in use", f"'{destination.name}' already exists.", parent=self.window); return
        try: source.rename(destination); self.refresh(); self.status_var.set(f"Renamed to {destination.name}")
        except OSError as error: self._error("rename the item", error)
    def copy_selected(self) -> None: self._transfer(False)
    def move_selected(self) -> None: self._transfer(True)
    def copy_path(self) -> None:
        path = self._selected()
        if path is None: return
        self.window.clipboard_clear(); self.window.clipboard_append(str(path)); self.status_var.set(f"Copied path: {path}")
    def reveal_selected(self) -> None:
        path = self._selected()
        if path is None: return
        try: subprocess.Popen(reveal_command(path))
        except OSError as error: self._error("show the item in its folder", error)
    def duplicate_selected(self) -> None:
        source = self._selected()
        if source is None: return
        destination = duplicate_destination(source)
        try:
            if source.is_dir(): shutil.copytree(source, destination)
            else: shutil.copy2(source, destination)
            self.refresh(); self.status_var.set(f"Created {destination.name}")
        except OSError as error: self._error("duplicate the item", error)
    def _transfer(self, move: bool) -> None:
        source = self._selected()
        if source is None: return
        folder = filedialog.askdirectory(title=f"{'Move' if move else 'Copy'} {source.name} to", initialdir=self.current_directory, parent=self.window)
        if not folder: return
        destination = Path(folder) / source.name
        if destination.exists(): messagebox.showwarning("Item already exists", "Choose a destination without an item of the same name.", parent=self.window); return
        try:
            if move: shutil.move(str(source), str(destination))
            elif source.is_dir(): shutil.copytree(source, destination)
            else: shutil.copy2(source, destination)
            self.refresh(); self.status_var.set(f"{'Moved' if move else 'Copied'} {source.name} to {folder}")
        except OSError as error: self._error("move the item" if move else "copy the item", error)
    def delete_selected(self) -> None:
        path = self._selected()
        if path is None: return
        if not messagebox.askyesno("Move to Trash?", f"Move '{path.name}' to the system Trash or Recycle Bin?", icon="warning", parent=self.window): return
        try:
            from send2trash import send2trash
            send2trash(str(path)); self.refresh(); self.status_var.set(f"Moved {path.name} to Trash")
        except OSError as error: self._error("move the item to Trash", error)
    def _error(self, operation: str, error: OSError) -> None: messagebox.showerror("File operation failed", f"ACCESS could not {operation}:\n{error}", parent=self.window)
    def close(self) -> None:
        if self.window.winfo_exists(): self.window.destroy()
        if self.on_close: self.on_close()
