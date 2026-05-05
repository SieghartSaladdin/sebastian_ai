# SEBASTIAN (Terminal AI Companion)

SEBASTIAN is an elegant, asynchronous, and intelligent terminal-based AI assistant. Powered by Langchain and local/cloud LLMs (via Ollama), it is designed to seamlessly integrate into your command-line workflow with a highly polished user interface.

## 🌟 Features

* **Elegant Terminal UI**: Built with `rich`, featuring styled text, custom ASCII headers, and dynamic loading spinners for a premium CLI experience.
* **Tool Calling (Agentic Capabilities)**: SEBASTIAN can automatically execute system tools when needed:
  * 🖥️ **System Monitoring**: Check CPU, RAM usage, and NVIDIA GPU status.
  * 📁 **File Operations**: List directory contents, read files, and write/edit files natively.
* **Persistent Memory**: Uses SQLite to store conversational history so you can pick up exactly where you left off. 
* **Session Management**: Support for multiple isolated chat sessions.
* **Asynchronous Streaming**: Lightning-fast, non-blocking token streaming and background tool execution without freezing the terminal.

## 🛠️ Prerequisites

* Python 3.10+
* `pip` package manager
* [Ollama](https://ollama.com/) (If running models locally)

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/SieghartSaladdin/sebastian_ai.git
   cd sebastian_ai
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## 🎮 Usage

Run the main application to start chatting with SEBASTIAN:

```bash
python main.py
```

### Slash Commands

You can use the following commands directly in the chat input:
* `/sessions` - View a list of all saved conversation sessions.
* `/session <name>` - Switch to an existing session.
* `/new <name>` - Create and switch to a brand new session.
* `/help` - View the help menu.
* `exit`, `quit`, `bye` - Gracefully close the application.

## 🏗️ Project Structure

* `main.py` - Application entry point and main UI loop.
* `app/ui.py` - Terminal UI components, custom styling, and async prompts.
* `app/llm_handler.py` - Core Langchain integration, streaming logic, and tool execution.
* `app/tools.py` - Custom system tools (CPU/GPU check, file ops) available to the AI.
* `app/memory.py` - SQLite-based conversation memory management.

## 🤝 Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.
