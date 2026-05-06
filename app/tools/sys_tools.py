# app/tools/sys_tools.py
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
