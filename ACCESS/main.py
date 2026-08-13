import argparse
import os
import platform

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    # The native GUI and offline command engine do not require dotenv.
    pass

from core.engine import AccessEngine


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "ACCESS"

APP_FULL_NAME = (
    "Adaptive Cognitive Companion for Efficient System Services\n"
)

APP_DESCRIPTION = "Intelligent Desktop Assistant"

VERSION = "1.0"
MODE = "OFFLINE-FIRST"

console = None


def _load_terminal_ui():
    """Load Rich only when the classic terminal interface is requested."""

    global Align, Console, Group, Panel, Table, Text, console
    if console is not None:
        return
    try:
        from rich.align import Align as RichAlign
        from rich.console import Console as RichConsole, Group as RichGroup
        from rich.panel import Panel as RichPanel
        from rich.table import Table as RichTable
        from rich.text import Text as RichText
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Terminal mode requires Rich. Run: pip install -r requirements.txt"
        ) from error

    Align = RichAlign
    Console = RichConsole
    Group = RichGroup
    Panel = RichPanel
    Table = RichTable
    Text = RichText
    console = Console()


# ============================================================
# BANNER
# ============================================================

def show_banner():
    """Display the main ACCESS banner."""

    # --------------------------------------------------------
    # ACCESS ASCII LOGO
    # --------------------------------------------------------

    logo = Text(
        "\n".join(
            [
                " █████╗  ██████╗ ██████╗███████╗███████╗███████╗",
                "██╔══██╗██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝",
                "███████║██║     ██║     █████╗  ███████╗███████╗",
                "██╔══██║██║     ██║     ██╔══╝  ╚════██║╚════██║",
                "██║  ██║╚██████╗╚██████╗███████╗███████║███████║",
                "╚═╝  ╚═╝ ╚═════╝╚═════╝╚══════╝╚══════╝╚══════╝",
            ]
        ),
        style="bold cyan",
        justify="center",
    )

    # --------------------------------------------------------
    # PROJECT NAME
    # --------------------------------------------------------

    full_name = Text(
        APP_FULL_NAME,
        style="bold white",
        justify="center",
    )

    # --------------------------------------------------------
    # DESCRIPTION
    # --------------------------------------------------------

    description = Text(
        APP_DESCRIPTION,
        style="dim",
        justify="center",
    )

    # --------------------------------------------------------
    # GROUP
    # --------------------------------------------------------

    content = Group(
        Align.center(logo),
        Text(""),
        Align.center(full_name),
        Align.center(description),
    )

    # --------------------------------------------------------
    # PANEL
    # --------------------------------------------------------

    console.print(
        Panel(
            Align.center(content),
            border_style="cyan",
            padding=(1, 2),
        )
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

def show_system_status(engine):
    """Display ACCESS system status."""

    table = Table(
        show_header=False,
        show_edge=False,
        box=None,
        padding=(0, 1),
        expand=False,
    )

    # --------------------------------------------------------
    # COLUMNS
    # --------------------------------------------------------

    table.add_column(
        "Component",
        style="bold cyan",
        no_wrap=True,
        justify="left",
    )

    table.add_column(
        "Separator",
        style="dim",
        no_wrap=True,
        justify="center",
    )

    table.add_column(
        "Status",
        no_wrap=True,
        justify="left",
    )

    # --------------------------------------------------------
    # STATUS ROWS
    # --------------------------------------------------------

    table.add_row(
        "SYSTEM",
        "│",
        "[green]● ONLINE[/green]",
    )

    table.add_row(
        "ENGINE",
        "│",
        "[green]● READY[/green]",
    )

    table.add_row(
        "ROUTER",
        "│",
        "[green]● READY[/green]",
    )

    table.add_row(
        "MODE",
        "│",
        f"[yellow]{MODE}[/yellow]",
    )

    table.add_row(
        "PLATFORM",
        "│",
        platform.system(),
    )

    table.add_row(
        "VERSION",
        "│",
        VERSION,
    )

    # --------------------------------------------------------
    # STATUS PANEL
    # --------------------------------------------------------

    console.print(
        Panel(
            table,
            title="[bold cyan]ACCESS STATUS[/bold cyan]",
            title_align="center",
            border_style="blue",
            padding=(1, 2),
        )
    )


# ============================================================
# HELP
# ============================================================

def show_help():
    """Display available commands."""

    table = Table(
        title="ACCESS Commands",
        title_style="bold cyan",
        border_style="cyan",
        padding=(0, 1),
    )

    table.add_column(
        "Command",
        style="bold cyan",
        no_wrap=True,
    )

    table.add_column(
        "Description",
    )

    commands = [
        ("help", "Show available commands"),
        ("status", "Show ACCESS system status"),
        ("about", "Show project information"),
        ("clear", "Clear the terminal"),
        ("exit", "Close ACCESS"),

        ("who are you", "Identify ACCESS"),
        ("open chrome", "Open an application"),
        ("close chrome", "Close an application"),

        ("screenshot", "Capture the screen"),

        ("brightness up", "Increase screen brightness"),
        ("brightness down", "Decrease screen brightness"),

        ("volume up", "Increase system volume"),
        ("volume down", "Decrease system volume"),
        ("mute", "Mute system audio"),

        ("turn on dark mode", "Enable dark mode"),
        ("turn on white mode", "Enable light mode"),

        ("create file NAME", "Create a file"),
        ("read file PATH", "Read a file"),
        ("search file NAME", "Search for a file"),
        ("copy file A to B", "Copy a file"),
        ("move file A to B", "Move a file"),
        ("rename file A to B", "Rename a file"),
        ("delete file PATH", "Delete a file"),
    ]

    for command, description in commands:
        table.add_row(
            command,
            description,
        )

    console.print()
    console.print(
        Align.center(table)
    )


# ============================================================
# ABOUT
# ============================================================

def show_about():
    """Display project information."""

    title = Text(
        APP_NAME,
        style="bold cyan",
        justify="center",
    )

    full_name = Text(
        APP_FULL_NAME,
        style="bold white",
        justify="center",
    )

    description = Text(
        "Hybrid Offline + Online AI Desktop Assistant",
        style="green",
        justify="center",
    )

    features = Text(
        "Cross-platform • Privacy-first • Modular • Extensible",
        style="dim",
        justify="center",
    )

    content = Group(
        Align.center(title),
        Align.center(full_name),
        Text(""),
        Align.center(description),
        Align.center(features),
    )

    console.print(
        Panel(
            Align.center(content),
            title="ABOUT",
            title_align="center",
            border_style="cyan",
            padding=(1, 2),
        )
    )


# ============================================================
# START ACCESS
# ============================================================

def start_access():
    """Start ACCESS."""

    _load_terminal_ui()

    engine = AccessEngine()

    console.clear()

    # --------------------------------------------------------
    # INITIAL INTERFACE
    # --------------------------------------------------------

    show_banner()

    console.print()

    show_system_status(engine)

    console.print()

    console.print(
        Align.center(
            Text.assemble(
                ("Type ", "dim"),
                ("'help'", "green"),
                (" to see available commands.", "dim"),
            )
        )
    )

    console.print()

    # --------------------------------------------------------
    # MAIN LOOP
    # --------------------------------------------------------

    while engine.running:

        try:
            command = console.input(
                "[bold cyan]ACCESS[/bold cyan] "
                "[white]>[/white] "
            ).strip()

        except (KeyboardInterrupt, EOFError):

            console.print(
                "\n[yellow]ACCESS shutting down...[/yellow]"
            )

            break

        # ----------------------------------------------------
        # EMPTY INPUT
        # ----------------------------------------------------

        if not command:
            continue

        command_lower = command.lower().strip()

        # ----------------------------------------------------
        # UI COMMANDS
        # ----------------------------------------------------

        if command_lower == "help":
            console.print()
            show_help()
            console.print()
            continue

        if command_lower == "status":
            console.print()
            show_system_status(engine)
            console.print()
            continue

        if command_lower == "about":
            console.print()
            show_about()
            console.print()
            continue

        # ----------------------------------------------------
        # CLEAR
        # ----------------------------------------------------

        if command_lower == "clear":

            console.clear()

            show_banner()

            console.print()

            show_system_status(engine)

            console.print()

            console.print(
                Align.center(
                    Text.assemble(
                        ("Type ", "dim"),
                        ("'help'", "green"),
                        (
                            " to see available commands.",
                            "dim",
                        ),
                    )
                )
            )

            console.print()

            continue

        # ----------------------------------------------------
        # ENGINE COMMAND
        # ----------------------------------------------------

        response = engine.process(command)

        console.print()

        console.print(
            f"[cyan]ACCESS:[/cyan] {response}"
        )

        console.print()


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    """Application entry point. The GUI is the default; ``--cli`` keeps the classic UI."""

    parser = argparse.ArgumentParser(description=APP_FULL_NAME)
    parser.add_argument(
        "--cli",
        action="store_true",
        help="run the classic terminal interface",
    )
    args = parser.parse_args()

    if args.cli:
        start_access()
        return

    try:
        from ui.gui import start_gui

        start_gui()
    except (ImportError, __import__("tkinter").TclError) as error:
        _load_terminal_ui()
        console.print(
            f"[yellow]GUI unavailable ({error}). Starting terminal mode.[/yellow]"
        )
        start_access()


if __name__ == "__main__":
    main()