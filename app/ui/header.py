# app/ui/header.py
import pyfiglet
from rich.text import Text
from rich.panel import Panel

from app.ui.console import console


def generate_title(text: str) -> Text:
    """Generate an ASCII art title using the slant font."""
    try:
        f = pyfiglet.Figlet(font='slant')
    except Exception:
        f = pyfiglet.Figlet(font='slant')

    ascii_art = f.renderText(text)
    return Text(ascii_art, style="sebastian")


def show_header():
    """Display the welcome header in the terminal."""
    console.clear()
    title = generate_title("SEBASTIAN")
    console.print(title)
    console.print("[dim]Terminal Agent v0.2 — Gemini CLI Experience[/dim]", justify="center")
    console.print("─" * console.width, style="dim")

    console.print(
        Panel(
            "Welcome! I am [sebastian]SEBASTIAN[/sebastian], your intelligent terminal companion.\n"
            "Type [bold cyan]/help[/bold cyan] for all commands · "
            "[bold cyan]@file.py[/bold cyan] to reference files · "
            "[bold red]/exit[/bold red] to quit.",
            title="[bold]Setup[/bold]",
            border_style="sebastian",
            padding=(1, 2)
        )
    )
