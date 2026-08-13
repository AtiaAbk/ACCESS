import argparse
import os

from core.engine import AccessEngine

# ============================================================
# CONFIGURATION
# ============================================================

try:
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:
    # The native GUI and offline command engine do not require dotenv.
    pass

APP_NAME = "ACCESS"
APP_FULL_NAME = (
    "Adaptive Cognitive Companion for Efficient System Services"
)

VERSION = "1.0"
MODE = "OFFLINE-FIRST"

console = None


def _load_terminal_ui():
    """Load Rich only when the classic terminal interface is requested."""

    global Align, Console, Panel, Table, Text, console
    if console is not None:
        return
    try:
        from rich.align import Align as RichAlign
        from rich.console import Console as RichConsole
        from rich.panel import Panel as RichPanel
        from rich.table import Table as RichTable
        from rich.text import Text as RichText
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Terminal mode requires Rich. Run: pip install -r requirements.txt"
        ) from error

    Align = RichAlign
    Console = RichConsole
    Panel = RichPanel
    Table = RichTable
    Text = RichText
    console = Console()

# ============================================================
# BANNER
# ============================================================

def show_banner():
    """Display the main ACCESS banner."""

    banner = Text()

    banner.append(
        " █████╗  ██████╗ ██████╗███████╗███████╗███████╗\n",
        style="bold cyan",
    )
    banner.append(
        "██╔══██╗██╔════╝██╔════╝██╔════╝██╔════╝██╔════╝\n",
        style="bold cyan",
    )
    banner.append(
        "███████║██║     ██║     █████╗  ███████╗███████╗\n",
        style="bold cyan",
    )
    banner.append(
        "██╔══██║██║     ██║     ██╔══╝  ╚════██║╚════██║\n",
        style="bold cyan",
    )
    banner.append(
        "██║  ██║╚██████╗╚██████╗███████╗███████║███████║\n",
        style="bold cyan",
    )
    banner.append(
        "╚═╝  ╚═╝ ╚═════╝╚═════╝╚══════╝╚══════╝╚══════╝",
        style="bold cyan",
    )

    subtitle = Text()

    subtitle.append(
        "\n\nAdaptive Cognitive Companion for Efficient System Services",
        style="bold white",
    )

    subtitle.append(
        "\n\nIntelligent Desktop Assistant",
        style="dim",
    )

    content = Text.assemble(
        banner,
        subtitle
    )

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
        box=None,
        padding=(0, 2),
    )

    table.add_row(
        "[bold cyan]SYSTEM[/bold cyan]",
        "[green]● ONLINE[/green]",
    )

    table.add_row(
        "[bold cyan]ENGINE[/bold cyan]",
        "[green]● READY[/green]",
    )

    table.add_row(
        "[bold cyan]ROUTER[/bold cyan]",
        "[green]● READY[/green]",
    )

    table.add_row(
        "[bold cyan]MODE[/bold cyan]",
        f"[yellow]{MODE}[/yellow]",
    )

    table.add_row(
        "[bold cyan]PLATFORM[/bold cyan]",
        os.name if os.name != "posix" else __import__("platform").system(),
    )

    table.add_row(
        "[bold cyan]VERSION[/bold cyan]",
        VERSION,
    )

    console.print(
        Panel(
            table,
            title="[bold cyan]ACCESS STATUS[/bold cyan]",
            border_style="blue",
        )
    )

# ============================================================
# HELP
# ============================================================

def show_help():
    """Display available commands."""

    table = Table(
        title="ACCESS Commands",
        border_style="cyan",
    )

    table.add_column(
        "Command",
        style="bold cyan"
    )

    table.add_column(
        "Description"
    )

    commands = [
        ("help", "Show available commands"),
        ("status", "Show ACCESS system status"),
        ("about", "Show project information"),
        ("clear", "Clear the terminal"),
        ("exit", "Close ACCESS"),
        ("open chrome", "Open an application"),
        ("close chrome", "Close an application"),
        ("screenshot", "Capture the screen"),
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
            description
        )

    console.print(table)

# ============================================================
# ABOUT
# ============================================================

def show_about():
    """Display project information."""

    info = Text()

    info.append(
        "ACCESS\n",
        style="bold cyan",
    )

    info.append(
        "Adaptive Cognitive Companion for Efficient System Services\n\n",
        style="bold white",
    )

    info.append(
        "Hybrid Offline + Online AI Desktop Assistant\n",
        style="green",
    )

    info.append(
        "Cross-platform • Privacy-first • Modular • Extensible",
        style="dim",
    )

    console.print(
        Panel(
            Align.center(info),
            title="ABOUT",
            border_style="cyan",
        )
    )

# ============================================================
# MAIN APPLICATION
# ============================================================

def start_access():
    """Start ACCESS."""

    _load_terminal_ui()

    engine = AccessEngine()

    console.clear()

    show_banner()

    console.print()

    show_system_status(engine)

    console.print()

    console.print(
        "[dim]Type 'help' to see available commands.[/dim]"
    )

    console.print()

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

        if not command:
            continue

        command_lower = command.lower()

        # UI-only commands
        if command_lower == "help":
            show_help()
            continue

        if command_lower == "status":
            show_system_status(engine)
            continue

        if command_lower == "about":
            show_about()
            continue

        if command_lower == "clear":
            console.clear()
            show_banner()
            console.print()
            continue

        # Everything else goes to the engine
        response = engine.process(command)

        console.print(
            f"[cyan]ACCESS:[/cyan] {response}"
        )

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
