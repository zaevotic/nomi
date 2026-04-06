#literally, the brain# main.py

import os, json, argparse, yaml, google.generativeai as genai, sqlite3, sys
os.environ["GRPC_VERBOSITY"] = "NONE"
os.environ["GRPC_TRACE"] = ""
os.environ["ABSL_MIN_LOG_LEVEL"] = "3"
from dotenv import load_dotenv
from datetime import datetime, timezone
# Model selection: use config default_model or hardcoded fallback
from src.load_chat import choose_chat
from src.utils.cli import get_user_input
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()
console = Console()
class Brain:
    def __init__(self, config, chat_name=None, chat_id=None, log_callback=None):
        """
        Data from config and .env so that the bot can work
        """
        # Store log callback
        self.log_callback = log_callback

        # experimental stuff
        self.conn = sqlite3.connect("nomi_memory.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.console = Console()
        self.config = config
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.persona = config.get("persona", "")
        # Try to get a model from config, else use a direct default without probing
        self.model_name = config.get("default_model") or "gemini-2.5-flash"
        self._log(f"Using model: {self.model_name}", "info")

        # UI settings (optional)
        ui_config = self.config.get("ui", {})
        self.show_timestamps = ui_config.get("show_timestamps", True)
        self.animation_enabled = ui_config.get("animation_enabled", True)

        # --- Chat resolution logic ---
        if chat_id is not None and chat_name is not None:
            # Passed directly (e.g. from TUI)
            self.chat_id = chat_id
            self.chat_name = chat_name
        elif "force_chat" in self.config:
            # Config forces a specific chat
            self.cursor.execute("SELECT id FROM chats WHERE name=?", (self.config["force_chat"],))
            row = self.cursor.fetchone()
            if row:
                self.chat_id = row[0]
                self.chat_name = self.config["force_chat"]
            else:
                self.cursor.execute("INSERT INTO chats (name) VALUES (?)", (self.config["force_chat"],))
                self.conn.commit()
                self.chat_id = self.cursor.lastrowid
                self.chat_name = self.config["force_chat"]
        else:
            # Interactive fallback (not used in TUI)
            self.chat_id, self.chat_name = self.choose_chat_db()

        # --- Load existing history ---
        self.cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp ASC",
            (self.chat_id,)
        )
        rows = self.cursor.fetchall()
        self.history = [
            {"role": role, "parts": [content], "timestamp": timestamp}
            for role, content, timestamp in rows
        ]

        # Build full_history without timestamps for Gemini context (only this chat)
        # Already filtered by chat_id in the query above - just convert format
        self.full_history = [
            {"role": role, "parts": [{"text": content}]}
            for role, content, _ in [(r[0], r[1], r[2]) for r in rows]
        ]

        # --- API Setup ---
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in .env file.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(
            self.model_name,
            system_instruction=self.persona
        )
        self.chat_session = self.model.start_chat(
            history=self.full_history
        )

    def _log(self, message: str, level: str = "info"):
        """Log to UI callback if set, otherwise to console."""
        if self.log_callback:
            try:
                self.log_callback(message, level)
            except Exception as e:
                self.console.print(f"[{level}]{message}[/{level}] (callback error: {e})")
        else:
            self.console.print(f"[{level}]{message}[/{level}]")

    def choose_chat_db(self):
        self.cursor.execute("SELECT id, name FROM chats ORDER BY created_at ASC")
        chats = self.cursor.fetchall()

        if not chats:
            name = input("No chats found. Enter new chat name: ").strip()
            self.cursor.execute("INSERT INTO chats (name) VALUES (?)", (name,))
            self.conn.commit()
            chat_id = self.cursor.lastrowid
            return chat_id, name

        print("Available chats:")
        for i, (chat_id, name) in enumerate(chats, 1):
            print(f"{i}. {name}")

        choice = input("Select a chat by number or enter new chat name: ").strip()

        if choice.isdigit() and 1 <= int(choice) <= len(chats):
            chat_id, name = chats[int(choice)-1]
        else:
            name = choice
            self.cursor.execute("INSERT INTO chats (name) VALUES (?)", (name,))
            self.conn.commit()
            chat_id = self.cursor.lastrowid

        return chat_id, name

    def generate_response(self, user_input: str, user_ts: datetime) -> tuple:
        """
        Generate a response to user input.
        Returns (response_text, model_ts) tuple.
        """
        try:
            self._log(f"Sending to {self.model_name}: {user_input[:50]}...", "info")

            import time
            start_time = time.time()

            # Call Gemini API (no spinner in TUI)
            response = self.chat_session.send_message(user_input)

            model_ts = datetime.now(timezone.utc)

            # Thread-safe: create a new cursor for this thread
            cursor = self.conn.cursor()

            # Save user message with provided timestamp
            cursor.execute(
                "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.chat_id, "user", user_input, user_ts.isoformat() if hasattr(user_ts, 'isoformat') else str(user_ts))
            )
            # Save model response
            cursor.execute(
                "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.chat_id, "model", response.text.strip(), model_ts.isoformat() if hasattr(model_ts, 'isoformat') else str(model_ts))
            )
            self.conn.commit()
            cursor.close()

            # Append to history with timestamps (thread-safe since only this thread modifies its own brain)
            self.history.append({
                "role": "user",
                "parts": [user_input],
                "timestamp": user_ts
            })
            self.history.append({
                "role": "model",
                "parts": [response.text.strip()],
                "timestamp": model_ts
            })

            # Also update full_history (without timestamps)
            self.full_history.append({"role": "user", "parts": [{"text": user_input}]})
            self.full_history.append({"role": "model", "parts": [{"text": response.text.strip()}]})

            latency = time.time() - start_time
            self._log(f"Response ({len(response.text)} chars, {latency:.2f}s)", "info")

            return response.text.strip(), model_ts

        except Exception as e:
            self._log(f"API error: {e}", "error")
            return f"[bold red]Error: Something went wrong: {e}[/bold red]", None

    def chat(self):
        # Legacy method for CLI mode; not used in TUI
        pass
