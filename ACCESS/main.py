import platform

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.engine import AccessEngine


APP_NAME = "ACCESS"
APP_FULL_NAME = (
    "Adaptive Cognitive Companion for Efficient System Services"
)
VERSION = "1.0"
MODE = "OFFLINE-FIRST"

console = Console()


def show_banner():
    """Display the main ACCESS terminal banner."""

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

    content = Text.assemble(banner, subtitle)

    console.print(
        Panel(
            Align.center(content),
            border_style="cyan",
            padding=(1, 2),
        )
    )


def show_system_status():
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
        "[bold cyan]MODE[/bold cyan]",
        f"[yellow]{MODE}[/yellow]",
    )

    table.add_row(
        "[bold cyan]PLATFORM[/bold cyan]",
        platform.system(),
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


def show_help():
    """Display available terminal commands."""

    table = Table(
        title="ACCESS Commands",
        border_style="cyan",
    )

    table.add_column("Command", style="bold cyan")
    table.add_column("Description")

    table.add_row(
        "help",
        "Show available commands",
    )

    table.add_row(
        "status",
        "Show ACCESS system status",
    )

    table.add_row(
        "about",
        "Show project information",
    )

    table.add_row(
        "clear",
        "Clear the terminal",
    )

    table.add_row(
        "exit",
        "Close ACCESS",
    )

    console.print(table)


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


def start_access():
    """Start the ACCESS terminal interface."""

    engine = AccessEngine()

    console.clear()

    show_banner()

    console.print()

    show_system_status()

    console.print()

    console.print(
        "[dim]Type 'help' to see available commands.[/dim]"
    )

    console.print()

    while engine.running:

        try:
            command = console.input(
                "[bold cyan]ACCESS[/bold cyan] [white]>[/white] "
            ).strip()

        except (KeyboardInterrupt, EOFError):
            console.print(
                "\n[yellow]ACCESS shutting down...[/yellow]"
            )
            engine.stop()
            break

        if not command:
            continue

        command_lower = command.lower()

        if command_lower == "exit":
            engine.stop()

            console.print(
                "\n[cyan]ACCESS:[/cyan] "
                "[green]Session terminated safely.[/green]"
            )

        elif command_lower == "help":
            show_help()

        elif command_lower == "status":
            show_system_status()

        elif command_lower == "about":
            show_about()

        elif command_lower == "clear":
            console.clear()
            show_banner()

        else:
            response = engine.process(command)

            console.print(
                f"[cyan]ACCESS:[/cyan] {response}"
            )


def main():
    """Application entry point."""

    start_access()


if __name__ == "__main__":
    main()