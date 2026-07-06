# Nomi - Your AI Assistant with Memory

Nomi is a smart, CLI-based AI assistant designed for local interaction using Google's Gemini API. It remembers your chats, supports multiple sessions, and features cross-chat recall.

---

## Features

- Supports Gemini models (`gemini-1.5-flash-002`, etc.)
- Cross-chat recalling - different chats are linked and share context
- Multi-session chat - manage multiple conversations (like ChatGPT)
- SQLite storage - all conversations stored locally in a database
- Rich CLI interface - beautiful terminal UI powered by `rich`
- Dynamic model selection - automatically selects available Gemini models
- Cross-platform - works on both Linux and Windows
- First-launch checks - validates setup and configuration on first run
- Vector database preparation - groundwork for Retrieval-Augmented Generation (RAG)

---

## Current Project Progress

The project is currently in active development. Here is the current state of Nomi:

### Completed Features & Architecture
- Abstract Provider base class created with full Gemini and Local (Ollama) provider implementations.
- Cross-session memory and chat history loading from DB for both cloud and local models.
- Settings menu consolidation (Persona, Appearance, Model Selection, API, Plugins).
- Lazy provider loading and dynamic model selection.
- Core CLI and chat functionality, including `/copy` slash command.
- Persistent SQLite storage with DB creation and migrations.
- Terminal launch support across Linux, macOS, and Windows.
- Chat management features (rename validation, delete confirmation, metadata display).

### In Progress & Planned Features
- **Hybrid AI Backend (Memory):** Semantic event memory (vector embeddings), Document RAG (PDF/Markdown ingestion), and a curated Facts Store to reduce hallucination.
- **Multi-Provider Support:** Implementations for OpenRouter, OpenAI, and Anthropic APIs.
- **Advanced Capabilities:** Vision pipeline (image/video captioning), web scraping, and file upload support.
- **TUI & UX Improvements:** Full-window TUI, plugin system integration, chat search, and better error handling for API failures.
- **Multi-user chat support.**

---

## Folder Structure

```
 .
├──  config.yaml           # User configuration & preferences (auto-generated)
├──  exports               # Directory for exported chat logs (e.g., Markdown/JSON)
├──  nomi.py               # Main entry point for the application
├──  nomi_memory.db        # SQLite database storing all chat history (auto-generated)
├── 󰂺 README.md             # Project documentation
├──  requirements.txt      # Python dependencies
├── 󰣞 src                   # Source code directory
│   ├──  __init__.py
│   ├──  brain.py          # Core chat loop and database interaction logic
│   ├──  chat_ui.py        # UI rendering and layout components
│   ├──  menu.py           # Interactive CLI menus and settings
│   ├──  providers         # AI model provider implementations
│   │   ├──  __init__.py
│   │   ├──  anthropic.py  # Claude API integration (planned)
│   │   ├──  gemini.py     # Google Gemini API integration
│   │   ├──  local.py      # Local Ollama integration (e.g., Qwen2.5)
│   │   ├──  openai.py     # OpenAI API integration (planned)
│   │   └──  openrouter.py # OpenRouter API integration (planned)
│   ├──  tofetchmodal.py   # Dynamic fetching of available Gemini models
│   ├──  tui               # Experimental Terminal UI components (empty/planned)
│   └──  utils             # Helper functions and utilities
│       ├──  __init__.py
│       └──  cli.py        # CLI input handling and prompt styling
└──  TODOS.md              # Project roadmap and implementation plans
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/serpmillers/nomi
```

### 2. Navigate into the Directory

```bash
cd nomi
```

### 3. Create and activate a virtual environment

I used `pyenv` to install and manage Python version 3.13 in my repository, because `pydantic-core` was facing issues on 3.14.

```bash
sudo pacman -S pyenv

# Add this to your shell config (e.g., ~/.bashrc or ~/.zshrc)
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# After you've sourced the config file / opened a new terminal window:
pyenv install 3.13
pyenv local 3.13                    # Set local version (or rely on .python-version) 
python3 -m venv .venv               # create the environment
source .venv/bin/activate           # activate it (Linux/macOS)
# OR
.venv\Scripts\activate              # activate it (Windows)
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up Environment Variables

Create a `.env` file in the root directory with:

```
GEMINI_API_KEY='your_api_key_goes_here'
```

Or let the client take care of initialization and input the key in the interactive menu

> Get your API key from: https://aistudio.google.com/app/apikey

### 6. Run Nomi

```bash
python3 nomi.py
```

---

## How to Use

Upon first launch, Nomi will perform setup checks and guide you through configuration. The interactive menu provides access to:

- Start new chat sessions
- View and resume past conversations
- Switch between different models
- Configure settings
- Access chat history and logs

Chats are automatically saved to `nomi_memory.db` and can be recalled across sessions.
