# app/ui/renderers.py
import os
import difflib
import pathlib

from rich.syntax import Syntax
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from app.ui.console import console


# ─── File Viewer (Syntax Highlighted) ───────────────────────────────

def render_file(path: str, max_inline_lines: int = 200) -> None:
    """Display a file with syntax highlighting, line numbers, and auto-paging."""
    if not os.path.isfile(path):
        _render_error("File not found", f"'{path}' does not exist.", "Check the path with /ls or use an absolute path.")
        return

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        _render_error("Binary file", f"'{path}' is not a text file.", "Only text files can be displayed.")
        return

    line_count = content.count('\n') + 1
    file_size = os.path.getsize(path)
    subtitle = f"{line_count} lines · {file_size:,} bytes"

    syntax = Syntax(
        content,
        lexer=Syntax.guess_lexer(path, code=content),
        line_numbers=True,
        theme="monokai",
        indent_guides=True,
        word_wrap=True,
        padding=(1, 2),
    )
    panel = Panel(
        syntax,
        title=f"[bold cyan]📄 {path}[/bold cyan]",
        subtitle=f"[dim]{subtitle}[/dim]",
        border_style="cyan",
    )

    if line_count > max_inline_lines:
        with console.pager(styles=True):
            console.print(panel)
    else:
        console.print(panel)


# ─── Directory Tree ─────────────────────────────────────────────────

_FILE_ICONS = {
    ".py": "🐍", ".js": "🟨", ".ts": "🔷", ".json": "📋",
    ".md": "📝", ".txt": "📄", ".env": "🔑", ".html": "🌐",
    ".css": "🎨", ".sql": "🗄️", ".sh": "⚙️", ".yml": "📐",
    ".yaml": "📐", ".toml": "📐", ".xml": "📐", ".csv": "📊",
    ".jpg": "🖼️", ".png": "🖼️", ".gif": "🖼️", ".svg": "🖼️",
    ".zip": "📦", ".gz": "📦", ".tar": "📦",
}

_IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode", ".mypy_cache", ".pytest_cache"}


def render_tree(path: str = ".", max_depth: int = 3) -> None:
    """Display a directory tree with icons and file sizes."""
    p = pathlib.Path(path).resolve()
    if not p.is_dir():
        _render_error("Not a directory", f"'{path}' is not a valid directory.", "Provide a valid directory path.")
        return

    root = Tree(f"[bold cyan]📁 {p.name}/[/bold cyan]")
    file_count, dir_count = _build_tree(root, p, max_depth, 0)

    console.print(Panel(
        root,
        subtitle=f"[dim]{dir_count} dirs · {file_count} files[/dim]",
        border_style="dim",
    ))


def _build_tree(tree_node, path: pathlib.Path, max_depth: int, depth: int) -> tuple:
    """Recursively build tree. Returns (file_count, dir_count)."""
    file_count = 0
    dir_count = 0

    if depth >= max_depth:
        tree_node.add("[dim italic]... (max depth reached)[/dim italic]")
        return 0, 0

    try:
        entries = sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
    except PermissionError:
        tree_node.add("[red]⛔ Permission denied[/red]")
        return 0, 0

    for entry in entries:
        if entry.name in _IGNORE_DIRS:
            continue

        if entry.is_dir():
            dir_count += 1
            branch = tree_node.add(f"📁 [bold]{entry.name}/[/bold]")
            fc, dc = _build_tree(branch, entry, max_depth, depth + 1)
            file_count += fc
            dir_count += dc
        else:
            file_count += 1
            icon = _FILE_ICONS.get(entry.suffix.lower(), "📄")
            try:
                size = entry.stat().st_size
                size_str = _human_size(size)
            except OSError:
                size_str = "?"
            tree_node.add(f"{icon} {entry.name} [dim]{size_str}[/dim]")

    return file_count, dir_count


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:,.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


# ─── Diff Viewer ────────────────────────────────────────────────────

def render_diff(old_content: str, new_content: str, file_path: str) -> None:
    """Show a colored unified diff before confirming a file write."""
    if not old_content:
        # New file — just show the new content
        syntax = Syntax(
            new_content,
            lexer=Syntax.guess_lexer(file_path, code=new_content),
            line_numbers=True,
            theme="monokai",
            padding=(1, 2),
        )
        console.print(Panel(
            syntax,
            title=f"[bold green]✨ New file: {file_path}[/bold green]",
            border_style="green",
        ))
        return

    diff_lines = list(difflib.unified_diff(
        old_content.splitlines(keepends=True),
        new_content.splitlines(keepends=True),
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
    ))

    if not diff_lines:
        console.print(f"  [dim]No changes to {file_path}[/dim]")
        return

    text = Text()
    for line in diff_lines:
        if line.startswith('+') and not line.startswith('+++'):
            text.append(line, style="bold green")
        elif line.startswith('-') and not line.startswith('---'):
            text.append(line, style="bold red")
        elif line.startswith('@@'):
            text.append(line, style="bold cyan")
        else:
            text.append(line, style="dim")

    console.print(Panel(
        text,
        title=f"[bold yellow]📝 Changes: {file_path}[/bold yellow]",
        border_style="yellow",
    ))


# ─── Help Table ─────────────────────────────────────────────────────

def render_help() -> None:
    """Display a styled table of all slash commands."""
    table = Table(title="[bold cyan]Sebastian Commands[/bold cyan]", border_style="dim", show_lines=True)
    table.add_column("Command", style="bold green", min_width=18)
    table.add_column("Description", style="white")

    commands = [
        ("/help", "Show this help table"),
        ("/ls [path] [depth]", "Display directory tree (default: cwd, depth 3)"),
        ("/read <file>", "View file with syntax highlighting"),
        ("/cd <path>", "Change working directory"),
        ("/sessions", "List all chat sessions"),
        ("/session <name>", "Switch to a session (creates if new)"),
        ("/history", "Page through conversation history"),
        ("/clear", "Clear the screen"),
        ("/exit", "Exit Sebastian"),
        ("@file.py ...", "Include file contents in your prompt"),
    ]
    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)


# ─── Error Renderer ─────────────────────────────────────────────────

def _render_error(what: str, cause: str, fix: str) -> None:
    """Display a 3-part actionable error message."""
    console.print(f"\n  [bold red]❌ {what}[/bold red]")
    console.print(f"     [dim]Cause:[/dim] {cause}")
    console.print(f"     [dim]Fix:[/dim]   {fix}\n")


def render_error(what: str, cause: str, fix: str) -> None:
    """Public error renderer — 3-part format like Claude Code."""
    _render_error(what, cause, fix)
