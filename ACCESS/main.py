import os

from dotenv import load_dotenv
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.engine import AccessEngine


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

APP_NAME = "ACCESS"
APP_FULL_NAME = (
    "Adaptive Cognitive Companion for Efficient System Services"
)

VERSION = "1.0"
MODE = "OFFLINE-FIRST"

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
        "╚═╝  ╚═╝ ╚═════╝ ╚═════╝╚══════╝╚══════╝╚══════╝",
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
        os.uname().sysname,
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
    """Application entry point."""

    start_access()


if __name__ == "__main__":
    main()