# app/tools/__init__.py
from app.tools.sys_tools import check_cpu_ram, check_gpu_status
from app.tools.fs_tools import list_directory, read_file, write_file

# Master list used by llm_handler to bind tools to the LLM
ALL_TOOLS = [check_cpu_ram, check_gpu_status, list_directory, read_file, write_file]
TOOLS_MAP = {tool.name: tool for tool in ALL_TOOLS}
