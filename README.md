# 🧠 Nomi – Your AI Assistant with Memory

Nomi is a smart, CLI-based AI assistant designed for local interaction using Google's Gemini API. It remembers your chats, supports multiple sessions, and features cross-chat recall.

---

## 🚀 Features

- ✅ Supports Gemini models (`gemini-1.5-flash-002`, etc.)
- 🔗 **Cross-chat recalling** - different chats are linked and share context
- 💬 **Multi-session chat** - manage multiple conversations (like ChatGPT)
- 🗄️ **SQLite storage** - all conversations stored locally in a database
- 🖥️ **Rich CLI interface** - beautiful terminal UI powered by `rich`
- ⚡ **Dynamic model selection** - automatically selects available Gemini models
- 🖥️ **Cross-platform** - works on both Linux and Windows
- 🔍 **First-launch checks** - validates setup and configuration on first run
- 🧬 **Vector database preparation** - groundwork for Retrieval-Augmented Generation (RAG)

## Planned Features:
- 🧬 Vector database implementation for full RAG capabilities (preparations complete)
- 👥 Multi-user chat support
- 🌐 Web scraping integration
- 📄 File upload and processing
- 📤 Chat export functionality
- 🎨 Enhanced CLI formatting
- 🗣 Voice input/output capabilities

---

## 📁 Current Folder Structure

```
nomi/
│
├── src/
│   ├── brain.py          # Handles the chat loop and conversation logic
│   ├── chat_ui.py        # Chat interface components
│   ├── load_chat.py      # Manages loading chats from the database
│   ├── menu.py           # Interactive CLI menu for features
│   ├── startup.py        # Model selection and initialization
│   ├── tofetchmodal.py   # Dynamic model selection based on availability
│   ├── providers/        # Provider-specific implementations
│   ├── tui/              # Terminal UI components
│   └── utils/
│       └── cli.py        # CLI input handling utilities
│
├── nomi.py               # Main entry point
├── config.yaml           # Configuration file for settings (not tracked by git)
├── nomi_memory.db        # SQLite database storing all chats (not tracked by git)
├── requirements.txt      # Python package dependencies
├── .env                  # Gemini API key (not tracked by git)
└── README.md

```

---

## 🛠 Installation & Setup

### 1. **Clone the Repository**

```bash
git clone https://github.com/serpmillers/nomi
```

### 2. **Navigate into the Directory**

```bash
cd nomi
```

### 3. **Create and activate a virtual environment**

```bash
python3 -m venv .venv               # create the environment

source .venv/bin/activate           # activate it (Linux/macOS)
# OR
.venv\Scripts\activate              # activate it (Windows)
```

### 4. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 5. **Set up Environment Variables**

Create a `.env` file in the root directory with:

```
GEMINI_API_KEY='your_api_key_goes_here'
```

> Get your API key from: https://aistudio.google.com/app/apikey

### 6. **Run Nomi**

```bash
python3 nomi.py
```

---

## 💡 How to Use

Upon first launch, Nomi will perform setup checks and guide you through configuration. The interactive menu provides access to:

- Start new chat sessions
- View and resume past conversations
- Switch between different Gemini models
- Configure settings
- Access chat history and logs

Chats are automatically saved to `nomi_memory.db` and can be recalled across sessions. Cross-chat recall ensures that context is shared and maintained throughout your entire conversation history.

---

