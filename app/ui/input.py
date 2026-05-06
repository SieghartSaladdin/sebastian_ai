# app/ui/input.py
import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter, PathCompleter, ThreadedCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import ANSI


# ─── Slash-command completer with path sub-completers ───────────────

SLASH_COMMANDS = {
    '/help': None,
    '/sessions': None,
    '/session': None,
    '/new': None,
    '/read': PathCompleter(),
    '/ls': PathCompleter(only_directories=True),
    '/cd': PathCompleter(only_directories=True),
    '/clear': None,
    '/exit': None,
    '/history': None,
}

# Lazy-init to avoid NoConsoleScreenBufferError when imported outside a terminal
_session = None


def _get_session() -> PromptSession:
    global _session
    if _session is None:
        _session = PromptSession(
            history=FileHistory('.sebastian_history'),
            completer=ThreadedCompleter(
                NestedCompleter.from_nested_dict(SLASH_COMMANDS)
            ),
            auto_suggest=AutoSuggestFromHistory(),
        )
    return _session


async def async_prompt(prompt_text: str = "\033[1;32mYou\033[0m \u276f ") -> str:
    """Non-blocking prompt with tab completion and arrow-key history."""
    session = _get_session()
    return await asyncio.to_thread(
        session.prompt,
        ANSI(prompt_text)
    )


async def async_confirm(prompt_text: str = "Apply changes? [y/N] ") -> bool:
    """Simple yes/no confirmation prompt."""
    session = _get_session()
    answer = await asyncio.to_thread(
        session.prompt,
        ANSI(f"\033[1;33m{prompt_text}\033[0m")
    )
    return answer.strip().lower() in ('y', 'yes')
