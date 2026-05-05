# app/tools.py
import os
import subprocess
import psutil
from langchain_core.tools import tool

@tool
def check_cpu_ram() -> str:
    """Checks the current system's CPU and RAM usage percentages. Use this tool whenever the user asks about system resources, memory, or CPU load."""
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    return f"Current CPU Usage: {cpu}%. Current RAM Usage: {ram}%."

@tool
def check_gpu_status() -> str:
    """Checks the temperature and VRAM usage of the NVIDIA GPU. Use this tool whenever the user asks about GPU status, heat, temperature, or video memory."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=temperature.gpu,memory.used,memory.total', '--format=csv,noheader'], 
            capture_output=True, text=True
        )
        return f"GPU Temperature, Used VRAM, Total VRAM: {result.stdout.strip()}"
    except FileNotFoundError:
        return "The 'nvidia-smi' command was not found. Please ensure an NVIDIA GPU is present and drivers are correctly installed."

@tool
def list_directory(path: str = ".") -> str:
    """Lists the files and folders inside a specified directory. Use this tool when the user asks to see the contents of a folder, list files, or explore the directory structure. If the user doesn't specify a path, use '.' for the current directory."""
    try:
        files = os.listdir(path)
        if not files:
            return f"The directory '{path}' is empty."
        return f"Contents of '{path}': {', '.join(files)}"
    except FileNotFoundError:
        return f"Error: The directory '{path}' does not exist."
    except PermissionError:
        return f"Error: Permission denied to access '{path}'."
    except Exception as e:
        return f"Error reading directory '{path}': {str(e)}"

@tool
def write_file(file_path: str, content: str) -> str:
    """Creates a new file or overwrites an existing one with the provided content. Use this tool when the user asks to create a file, write code, or save a note."""
    try:
        # Using 'w' mode will create the file if it doesn't exist, or overwrite it if it does
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully created and wrote content to '{file_path}'."
    except Exception as e:
        return f"Error writing to file '{file_path}': {str(e)}"

@tool
def read_file(file_path: str) -> str:
    """Reads and returns the contents of a specified file. Use this tool when the user asks to read a file, view code, or check file contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: The file '{file_path}' does not exist."
    except Exception as e:
        return f"Error reading file '{file_path}': {str(e)}"