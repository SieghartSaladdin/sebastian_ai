# app/llm_handler.py
import os
import json
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, ToolMessage, AIMessageChunk

from app.tools import ALL_TOOLS, TOOLS_MAP

SYSTEM_PROMPT = (
    "You are SEBASTIAN, an elegant and intelligent terminal companion. "
    "Answer concisely in English. Use the provided tools immediately if the user asks about "
    "system resources, CPU, GPU temperatures, wants to list files in a directory, read a file, "
    "or wants to create/write to a file. "
    "When writing files, always provide the COMPLETE file content — not just snippets."
)


def initialize_llm():
    """Initializes the ChatOllama model and binds the tools."""
    llm = ChatOllama(model="qwen3-coder:480b-cloud", temperature=0.7)
    return llm.bind_tools(ALL_TOOLS)


# ─── Tool action descriptions ──────────────────────────────────────

_TOOL_ACTIONS = {
    "write_file": lambda args: f"Writing '{args.get('file_path', '...')}'",
    "read_file": lambda args: f"Reading '{args.get('file_path', '...')}'",
    "list_directory": lambda args: f"Scanning '{args.get('path', '.')}'",
    "check_cpu_ram": lambda _: "Analyzing system metrics",
    "check_gpu_status": lambda _: "Querying GPU sensors",
}


async def astream_response(llm, messages: list, on_write_confirm=None):
    """
    Handles the tool-calling loop and yields events for the UI.

    Yields:
        dict events:  {"type": "tool_start/tool_done/tool_error", ...}
        AIMessageChunk: streamed text tokens of the final AI response

    Args:
        on_write_confirm: async callback(file_path, old, new) -> bool
            Called when write_file needs user confirmation.
    """
    MAX_HISTORY = 10
    recent = messages[-MAX_HISTORY:] if len(messages) > MAX_HISTORY else messages
    full_messages = [SystemMessage(content=SYSTEM_PROMPT)] + recent

    # First LLM call
    response = await llm.ainvoke(full_messages)
    tools_used = 0

    # ── Tool-calling loop ───────────────────────────────────────────
    while response.tool_calls:
        full_messages.append(response)

        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            action_fn = _TOOL_ACTIONS.get(tool_name)
            action_text = action_fn(tool_args) if action_fn else f"Running {tool_name}"

            yield {"type": "tool_start", "content": action_text}
            tools_used += 1

            try:
                # ── Special handling for write_file (diff + confirm) ────
                if tool_name == "write_file":
                    # Execute the tool — it returns structured JSON, NOT writing yet
                    raw_result = await asyncio.to_thread(TOOLS_MAP[tool_name].invoke, tool_args)

                    try:
                        pending = json.loads(raw_result)
                    except (json.JSONDecodeError, TypeError):
                        pending = None

                    if pending and pending.get("action") == "write_pending":
                        fp = pending["file_path"]
                        old = pending["old_content"]
                        new = pending["new_content"]
                        exists = pending["file_exists"]

                        # Only confirm for EXISTING files
                        if exists and on_write_confirm:
                            yield {"type": "write_confirm", "file_path": fp, "old_content": old, "new_content": new}
                            approved = await on_write_confirm(fp, old, new)

                            if approved:
                                # Create parent dirs if needed
                                os.makedirs(os.path.dirname(fp) or ".", exist_ok=True)
                                with open(fp, 'w', encoding='utf-8') as f:
                                    f.write(new)
                                tool_result = f"Successfully updated '{fp}'."
                            else:
                                tool_result = f"User declined changes to '{fp}'. File was NOT modified."
                        else:
                            # New file — write directly with a notice
                            os.makedirs(os.path.dirname(fp) or ".", exist_ok=True)
                            with open(fp, 'w', encoding='utf-8') as f:
                                f.write(new)
                            tool_result = f"Successfully created new file '{fp}'."
                    else:
                        tool_result = raw_result
                else:
                    # ── Normal tool execution ───────────────────────────
                    tool_result = await asyncio.to_thread(TOOLS_MAP[tool_name].invoke, tool_args)

                yield {"type": "tool_done", "content": action_text, "tool_name": tool_name}

            except Exception as e:
                tool_result = f"Tool error: {str(e)}"
                yield {"type": "tool_error", "content": action_text, "error": str(e)}

            full_messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            ))

        # Next LLM call after tools
        yield {"type": "tool_start", "content": "Analyzing results"}
        response = await llm.ainvoke(full_messages)
        yield {"type": "tool_done", "content": "Analyzing results", "tool_name": "_internal"}

    # ── Yield tool stats ────────────────────────────────────────────
    yield {"type": "tools_summary", "count": tools_used}

    # ── Simulate streaming of the final AI response ─────────────────
    tokens = response.content.split(" ")
    for i, token in enumerate(tokens):
        content = token + (" " if i < len(tokens) - 1 else "")
        chunk = AIMessageChunk(content=content)

        if i == len(tokens) - 1:
            chunk.usage_metadata = getattr(response, 'usage_metadata', None)

        yield chunk
        await asyncio.sleep(0.02)