# app/tools/fs_tools.py
import os
import json
import pathlib
from langchain_core.tools import tool


@tool
def list_directory(path: str = ".") -> str:
    """Lists the files and folders inside a specified directory. Use this tool when the user asks to see the contents of a folder, list files, or explore the directory structure. If the user doesn't specify a path, use '.' for the current directory."""
    try:
        p = pathlib.Path(path).resolve()
        if not p.exists():
            return json.dumps({"error": "not_found", "message": f"Directory '{path}' does not exist.", "fix": "Check the path or use /ls to browse."})
        if not p.is_dir():
            return json.dumps({"error": "not_dir", "message": f"'{path}' is not a directory.", "fix": "Provide a directory path, not a file."})

        entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        if not entries:
            return f"The directory '{path}' is empty."

        lines = [f"Contents of '{path}':"]
        for entry in entries:
            if entry.name in ('.git', '__pycache__', 'node_modules', '.venv', 'venv'):
                continue
            if entry.is_dir():
                lines.append(f"  📁 {entry.name}/")
            else:
                try:
                    size = entry.stat().st_size
                    lines.append(f"  📄 {entry.name} ({size:,} bytes)")
                except OSError:
                    lines.append(f"  📄 {entry.name}")
        return "\n".join(lines)
    except PermissionError:
        return json.dumps({"error": "permission", "message": f"Permission denied for '{path}'.", "fix": "Try a different directory or run with elevated permissions."})
    except Exception as e:
        return f"Error reading directory '{path}': {str(e)}"


@tool
def read_file(file_path: str) -> str:
    """Reads and returns the contents of a specified file. Use this tool when the user asks to read a file, view code, or check file contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        line_count = content.count('\n') + 1
        return f"[File: {file_path} | {line_count} lines | {len(content)} chars]\n{content}"
    except FileNotFoundError:
        return json.dumps({
            "error": "not_found", "path": file_path,
            "message": f"File '{file_path}' does not exist.",
            "fix": "Check the path with /ls or use an absolute path."
        })
    except UnicodeDecodeError:
        return json.dumps({
            "error": "binary", "path": file_path,
            "message": f"'{file_path}' is a binary file and cannot be read as text.",
            "fix": "Only text-based files can be read."
        })
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """Creates a new file or overwrites an existing one with the provided content. Use this tool when the user asks to create a file, write code, or save a note."""
    old_content = ""
    file_exists = os.path.exists(file_path)

    if file_exists:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                old_content = f.read()
        except Exception:
            old_content = ""

    # Return a structured payload — llm_handler intercepts this to show diff + confirm
    return json.dumps({
        "action": "write_pending",
        "file_path": file_path,
        "file_exists": file_exists,
        "old_content": old_content,
        "new_content": content,
    })
