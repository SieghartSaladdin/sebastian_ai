import asyncio
import sys
from rich.live import Live
from rich.text import Text
from rich.spinner import Spinner
from rich.console import Group

from app.memory import get_chat_history, list_sessions
from app.ui import show_header, async_prompt, get_console
from app.llm_handler import initialize_llm, astream_response

async def main():
    console = get_console()
    show_header()
    
    try:
        llm = initialize_llm()
    except Exception as e:
        console.print(f"[error]Failed to initialize Ollama:[/error] {e}")
        return

    last_total_tokens = 0
    total_tokens_used = 0
    
    current_session = "default"
    history = get_chat_history(current_session)
    console.print(f"[info]Current Session: {current_session} (Type /help for menu)[/info]")
    
    while True:
        try:
            console.print(f'[dim] Token Usage: {last_total_tokens} | Total: {total_tokens_used} | Session: {current_session} [/dim]', justify="right")
            
            user_input = await async_prompt("[user]You[/user]")
            
            # --- SLASH COMMANDS BLOCK ---
            if user_input.startswith('/'):
                parts = user_input.split()
                cmd = parts[0].lower()
                
                if cmd == '/sessions':
                    sessions = list_sessions()
                    if sessions:
                        console.print(f"[info]Available sessions: {', '.join(sessions)}[/info]")
                    else:
                        console.print("[info]No sessions found.[/info]")
                    continue
                    
                elif cmd in ['/session', '/new']:
                    if len(parts) > 1:
                        current_session = parts[1]
                        history = get_chat_history(current_session)
                        console.print(f"[info]Switched to session: {current_session}[/info]")
                    else:
                        console.print(f"[warning]Usage: {cmd} <session_name>[/warning]")
                    continue
                    
                elif cmd == '/help':
                    console.print("[info]Commands:[/info] /sessions (view all), /session <name> (switch), /new <name> (create)")
                    continue
                    
                else:
                    console.print("[warning]Unknown command. Type /help[/warning]")
                    continue

            # --- NORMAL CHAT BLOCK ---
            if user_input.lower() in ['exit', 'quit', 'bye']:
                console.print("\n[sebastian]sebastian :[/sebastian] It was a pleasure chatting with you. Goodbye!", style="info")
                break
            
            if not user_input.strip():
                continue

            history.add_user_message(user_input)

            full_response = ""
            current_turn_tokens = 0
            
            # 1. Start the loading animation
            status = console.status("[sebastian]Sebastian is thinking...[/sebastian]", spinner="dots")
            status.start()
            
            # Create the stream generator
            stream = astream_response(llm, history.messages)
            
            try:
                # 2. Wait for the VERY FIRST chunk from the LLM
                first_chunk = await stream.__anext__()
                
                # 3. Stop the loading animation immediately once we get a response
                status.stop()
                
                display_text = Text("sebastian : ", style="sebastian")
                current_spinner = None
                
                with Live(display_text, console=console, refresh_per_second=15, vertical_overflow="visible") as live:
                    
                    def handle_chunk(chunk_item):
                        nonlocal full_response, current_turn_tokens, display_text, current_spinner
                        if isinstance(chunk_item, dict):
                            ctype = chunk_item.get("type")
                            if ctype == "ui_status":
                                display_text.append(Text.from_markup(chunk_item["content"]))
                                live.update(Group(display_text, current_spinner) if current_spinner else display_text)
                            elif ctype == "loader_start":
                                current_spinner = Spinner("dots", text=Text.from_markup(f"[cyan]{chunk_item['content']}...[/cyan]"))
                                live.update(Group(display_text, current_spinner))
                            elif ctype == "loader_stop":
                                current_spinner = None
                                live.update(display_text)
                        else:
                            full_response += chunk_item.content
                            if hasattr(chunk_item, 'usage_metadata') and chunk_item.usage_metadata:
                                current_turn_tokens = chunk_item.usage_metadata.get('total_tokens', current_turn_tokens)
                            
                            # Reset display text so tool statuses disappear cleanly when AI answers
                            display_text = Text("sebastian : ", style="sebastian")
                            display_text.append(full_response)
                            live.update(Group(display_text, current_spinner) if current_spinner else display_text)

                    # Process the first chunk we caught
                    handle_chunk(first_chunk)

                    # 4. Stream the rest of the chunks normally
                    async for chunk in stream:
                        handle_chunk(chunk)
                        
            except StopAsyncIteration:
                # Failsafe if the stream is totally empty
                status.stop()

            last_total_tokens = current_turn_tokens
            total_tokens_used += current_turn_tokens
            console.print()

            history.add_ai_message(full_response)

        except KeyboardInterrupt:
            raise KeyboardInterrupt
            
        except Exception as e:
            console.print(f"[error]error :[/error] {str(e)}")
            console.print()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[System] Session interrupted by user. Exiting...")
        sys.exit(0)