# app/ui/console.py
from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "sebastian": "bold cyan",
    "user": "bold green",
    "success": "bold green",
    "path": "bold yellow",
    "tool": "bold magenta",
})

console = Console(theme=custom_theme)

def get_console() -> Console:
    return console
