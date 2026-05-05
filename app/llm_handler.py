# app/llm_handler.py
import asyncio
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, ToolMessage, AIMessageChunk

from app.tools import check_cpu_ram, check_gpu_status, list_directory, write_file, read_file

tools_list = [check_cpu_ram, check_gpu_status, list_directory, write_file, read_file]
tools_map = {tool.name: tool for tool in tools_list}

def initialize_llm():
    """Initializes the ChatOllama model and binds the tools."""
    llm = ChatOllama(model="qwen3-coder-next:cloud", temperature=0.7)
    return llm.bind_tools(tools_list)

async def astream_response(llm, messages: list):
    """Handles the Tool Calling Loop and yields the final response."""
    MAX_HISTORY = 10 
    recent_messages = messages[-MAX_HISTORY:] if len(messages) > MAX_HISTORY else messages
    
    full_messages = [
        SystemMessage(content="You are SEBASTIAN, an elegant and intelligent terminal companion. Answer concisely in English. Use the provided tools immediately if the user asks about system resources, CPU, GPU temperatures, wants to list files in a directory, read a file, or wants to create/write to a file.")
    ] + recent_messages

    # First LLM call
    response = await llm.ainvoke(full_messages)
    
    # Tool Calling Loop
    while response.tool_calls:
        full_messages.append(response)
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Determine natural language action based on the tool
            action_text = f"Running {tool_name}"
            if tool_name == "write_file":
                action_text = f"Editing file '{tool_args.get('file_path', '...')}'"
            elif tool_name == "read_file":
                action_text = f"Reading file '{tool_args.get('file_path', '...')}'"
            elif tool_name == "list_directory":
                action_text = f"Scanning directory '{tool_args.get('path', '.')}'"
            elif tool_name == "check_cpu_ram":
                action_text = "Analyzing system metrics"
            elif tool_name == "check_gpu_status":
                action_text = "Querying NVIDIA GPU sensors"
            
            # 1. YIELD STATUS: STARTING TOOL LOADER
            yield {"type": "loader_start", "content": action_text}
            
            # Execute the tool
            selected_tool = tools_map[tool_name]
            tool_result = await asyncio.to_thread(selected_tool.invoke, tool_args)
            
            # 2. YIELD STATUS: TOOL FINISHED (We can stop loader, but then yield a success message)
            yield {"type": "loader_stop"}
            yield {"type": "ui_status", "content": f"\n  [bold green]✅ Done: {action_text}.[/bold green]\n\n"}
            
            full_messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            ))
        
        # Second LLM call after tool execution to get the final conversational response
        yield {"type": "loader_start", "content": "Analyzing results"}
        response = await llm.ainvoke(full_messages)
        yield {"type": "loader_stop"}

    # 3. Simulate Streaming for UI (The actual AI verbal response)
    tokens = response.content.split(" ")
    for i, token in enumerate(tokens):
        content = token + (" " if i < len(tokens)-1 else "")
        chunk = AIMessageChunk(content=content)
        
        if i == len(tokens) - 1:
            chunk.usage_metadata = getattr(response, 'usage_metadata', None)
            
        yield chunk
        await asyncio.sleep(0.02)