# ui.py
import pyfiglet
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.theme import Theme

# Custom theme for premium look
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "sebastian": "bold cyan",
    "user": "bold green"
})

console = Console(theme=custom_theme)

def generate_title(text: str) -> Text:
    """Generate an ASCII art title using a stylish font."""
    try:
        f = pyfiglet.Figlet(font='slant')
    except:
        f = pyfiglet.Figlet(font='slant')
    
    ascii_art = f.renderText(text)
    return Text(ascii_art, style="sebastian")

def show_header():
    """Display the welcome header in the terminal."""
    console.clear()
    title = generate_title("SEBASTIAN")
    console.print(title)
    console.print("[dim]Terminal Chatbot UI v0.1 (Async)[/dim]", justify="center")
    console.print("-" * console.width, style="dim")

    console.print(
        Panel(
            "Welcome! I am [sebastian]SEBASTIAN[/sebastian], your intelligent terminal companion.\nType [bold red]'exit'[/bold red], [bold red]'quit'[/bold red], or [bold red]'bye'[/bold red] to end our session.",
            title="[bold]Setup Message[/bold]",
            border_style="sebastian",
            padding=(1, 2)
        )
    )

async def async_prompt(prompt_text: str) -> str:
    """Wrap the synchronous rich prompt function in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(Prompt.ask, prompt_text)

def get_console() -> Console:
    return console