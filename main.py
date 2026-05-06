# main.py
import os
import re
import asyncio
import sys

from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
from rich.console import Group

from app.memory import get_chat_history, list_sessions
from app.ui import (
    show_header, async_prompt, async_confirm, get_console,
    render_file, render_tree, render_diff, render_help, render_error,
)
from app.llm_handler import initialize_llm, astream_response


# ─── @-file mention injection ──────────────────────────────────────

def inject_file_mentions(user_input: str) -> str:
    """Replace @path/to/file tokens with the file's contents inline."""
    mentions_found = []

    def _replacer(match):
        path = match.group(1)
        if os.path.isfile(path):
            try:
                content = open(path, 'r', encoding='utf-8').read()
                mentions_found.append(path)
                return f"\n```\n# {path}\n{content}\n```\n"
            except Exception:
                return match.group(0)
        return match.group(0)

    result = re.sub(r'@([\w./\\:~-]+)', _replacer, user_input)

    if mentions_found:
        console = get_console()
        for p in mentions_found:
            console.print(f"  [dim]📎 Attached:[/dim] [path]{p}[/path]")

    return result


# ─── Slash command handler ──────────────────────────────────────────

async def handle_slash_command(cmd: str, args: list, console, current_session: str, history):
    """
    Handles slash commands locally (no LLM needed).
    Returns (new_session, new_history) or (None, None) if session unchanged.
    Returns ("__exit__", None) to signal exit.
    """
    if cmd == '/help':
        render_help()

    elif cmd == '/ls':
        path = args[0] if args else "."
        depth = 3
        if len(args) >= 2:
            try:
                depth = int(args[1])
            except ValueError:
                pass
        render_tree(path, max_depth=depth)

    elif cmd == '/read':
        if args:
            render_file(args[0])
        else:
            console.print("[warning]Usage: /read <file_path>[/warning]")

    elif cmd == '/cd':
        if args:
            target = args[0]
            try:
                os.chdir(target)
                console.print(f"  [success]📂 Changed directory to:[/success] [path]{os.getcwd()}[/path]")
            except FileNotFoundError:
                render_error("Directory not found", f"'{target}' does not exist.", "Use /ls to browse available directories.")
            except PermissionError:
                render_error("Permission denied", f"Cannot access '{target}'.", "Try a different directory.")
        else:
            console.print(f"  [info]📂 Current directory:[/info] [path]{os.getcwd()}[/path]")

    elif cmd == '/sessions':
        sessions = list_sessions()
        if sessions:
            from rich.table import Table
            table = Table(title="[bold cyan]Sessions[/bold cyan]", border_style="dim")
            table.add_column("Session", style="bold green")
            table.add_column("Status", style="dim")
            for s in sessions:
                marker = "◀ active" if s == current_session else ""
                table.add_row(s, marker)
            console.print(table)
        else:
            console.print("[info]No sessions found yet.[/info]")

    elif cmd in ('/session', '/new'):
        if args:
            new_session = args[0]
            new_history = get_chat_history(new_session)
            console.print(f"  [success]✅ Switched to session:[/success] [bold]{new_session}[/bold]")
            return new_session, new_history
        else:
            console.print(f"[warning]Usage: {cmd} <session_name>[/warning]")

    elif cmd == '/history':
        msgs = history.messages
        if msgs:
            from rich.markdown import Markdown
            lines = []
            for m in msgs:
                role = "🟢 You" if m.type == "human" else "🔵 Sebastian"
                lines.append(f"### {role}\n{m.content}\n")
            with console.pager(styles=True):
                console.print(Markdown("\n---\n".join(lines)))
        else:
            console.print("[info]No messages in this session yet.[/info]")

    elif cmd == '/clear':
        show_header()

    elif cmd == '/exit':
        return "__exit__", None

    else:
        console.print(f"[warning]Unknown command '{cmd}'. Type /help for available commands.[/warning]")

    return None, None


# ─── Main loop ──────────────────────────────────────────────────────

async def main():
    console = get_console()
    show_header()

    try:
        llm = initialize_llm()
    except Exception as e:
        render_error("Failed to initialize LLM", str(e), "Check that Ollama is running and the model is available.")
        return

    last_total_tokens = 0
    total_tokens_used = 0
    tools_used_last = 0

    current_session = "default"
    history = get_chat_history(current_session)
    console.print(f"[info]Session: {current_session} · CWD: {os.getcwd()} · Type /help for commands[/info]")

    while True:
        try:
            # ── Status bar ──────────────────────────────────────────
            cwd_display = os.getcwd()
            console.print(
                f'[dim] Tokens: {last_total_tokens} | Total: {total_tokens_used} '
                f'| Session: {current_session} | CWD: {cwd_display} '
                f'| Tools: {tools_used_last} [/dim]',
                justify="right"
            )

            user_input = await async_prompt()

            # ── Slash commands (handled locally) ────────────────────
            if user_input.startswith('/'):
                parts = user_input.split()
                cmd = parts[0].lower()
                args = parts[1:]

                result_session, result_history = await handle_slash_command(
                    cmd, args, console, current_session, history
                )
                if result_session == "__exit__":
                    console.print("\n[sebastian]Sebastian:[/sebastian] Goodbye! 👋", style="info")
                    break
                if result_session:
                    current_session = result_session
                    history = result_history
                continue

            # ── Exit keywords ───────────────────────────────────────
            if user_input.lower() in ('exit', 'quit', 'bye'):
                console.print("\n[sebastian]Sebastian:[/sebastian] It was a pleasure chatting with you. Goodbye! 👋", style="info")
                break

            if not user_input.strip():
                continue

            # ── @-file mention injection ────────────────────────────
            processed_input = inject_file_mentions(user_input)
            history.add_user_message(processed_input)

            # ── Write confirmation callback ─────────────────────────
            async def on_write_confirm(file_path, old_content, new_content):
                render_diff(old_content, new_content, file_path)
                return await async_confirm(f"Apply changes to '{file_path}'? [y/N] ")

            full_response = ""
            current_turn_tokens = 0
            tools_used_last = 0

            # ── Phase 1: Tool execution (spinner per tool) ──────────
            stream = astream_response(llm, history.messages, on_write_confirm=on_write_confirm)

            # Show "thinking" spinner immediately so user knows it's working
            thinking_status = console.status(
                "[sebastian]Sebastian is thinking...[/sebastian]",
                spinner="dots"
            )
            thinking_status.start()

            current_status = None
            first_text_chunk = None

            async for event in stream:
                # Stop the initial thinking spinner on the very first event
                if thinking_status:
                    thinking_status.stop()
                    thinking_status = None

                if isinstance(event, dict):
                    etype = event.get("type")

                    if etype == "tool_start":
                        if current_status:
                            current_status.stop()
                        current_status = console.status(
                            f"[tool]⚡ {event['content']}...[/tool]",
                            spinner="dots"
                        )
                        current_status.start()

                    elif etype == "tool_done":
                        if current_status:
                            current_status.stop()
                            current_status = None
                        tool_name = event.get("tool_name", "")
                        if tool_name != "_internal":
                            console.print(f"  [success]✅ {event['content']}[/success]")

                    elif etype == "tool_error":
                        if current_status:
                            current_status.stop()
                            current_status = None
                        console.print(f"  [error]❌ {event['content']}: {event.get('error', '')}[/error]")

                    elif etype == "write_confirm":
                        # Diff + confirm is handled by the callback — this event is informational
                        if current_status:
                            current_status.stop()
                            current_status = None

                    elif etype == "tools_summary":
                        tools_used_last = event.get("count", 0)

                else:
                    # First AIMessageChunk — switch to streaming phase
                    first_text_chunk = event
                    break

            if thinking_status:
                thinking_status.stop()
            if current_status:
                current_status.stop()

            # ── Phase 2: Stream AI response (Live display) ──────────
            if first_text_chunk:
                full_response += first_text_chunk.content
                if hasattr(first_text_chunk, 'usage_metadata') and first_text_chunk.usage_metadata:
                    current_turn_tokens = first_text_chunk.usage_metadata.get('total_tokens', 0)

                display_text = Text("Sebastian : ", style="sebastian")
                display_text.append(full_response)

                with Live(display_text, console=console, refresh_per_second=15, vertical_overflow="visible") as live:
                    async for chunk in stream:
                        if isinstance(chunk, dict):
                            continue  # Shouldn't happen here, but be safe

                        full_response += chunk.content
                        if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                            current_turn_tokens = chunk.usage_metadata.get('total_tokens', current_turn_tokens)

                        display_text = Text("Sebastian : ", style="sebastian")
                        display_text.append(full_response)
                        live.update(display_text)

            last_total_tokens = current_turn_tokens
            total_tokens_used += current_turn_tokens
            console.print()

            if full_response:
                history.add_ai_message(full_response)

        except KeyboardInterrupt:
            raise KeyboardInterrupt

        except Exception as e:
            render_error("Unexpected error", str(e), "Try again or check /help for options.")
            console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[System] Session interrupted by user. Exiting...")
        sys.exit(0)