# Core chat logic - no UI/console output. All presentation handled by ChatRenderer.

import os, json, yaml, sqlite3
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
from src.menu import edit_config

# Import base provider class (lightweight)
from src.providers import Provider

load_dotenv()


class Brain:
    """
    Core chat logic - no UI/console output.
    All presentation handled by ChatRenderer.

    Uses a Provider abstraction to support multiple AI backends.
    """

    def __init__(self, config, chat_name=None, chat_id=None):
        """
        Initialize brain with config and chat context.
        Provider is NOT loaded yet - call initialize_provider() separately.

        Args:
            config: dict with persona, ui settings, provider, default_model, etc.
            chat_name: name of chat
            chat_id: database ID (provided or fetched from name)
        """
        # DB setup
        self.conn = sqlite3.connect("nomi_memory.db")
        self.cursor = self.conn.cursor()

        self.config = config
        self.persona = config.get("persona", "")

        # UI settings
        ui_config = config.get("ui", {})
        self.show_timestamps = ui_config.get("show_timestamps", True)
        self.animation_enabled = ui_config.get("animation_enabled", True)

        # Provider setup (not initialized yet)
        self.provider_name = config.get("provider", "gemini")
        self.provider_class = self._get_provider_class(self.provider_name)
        self.provider: Optional[Provider] = None
        self.load_error: Optional[str] = None  # For initialization errors

        # Model state
        self.model_name = config.get("default_model")
        self.chat_session = None  # Delegate to provider

        # --- Chat resolution ---
        if chat_id is not None and chat_name is not None:
            self.chat_id = chat_id
            self.chat_name = chat_name
        elif "force_chat" in self.config:
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
            self.chat_id, self.chat_name = self.choose_chat_db()

        # --- Load history (for display) ---
        self.cursor.execute(
            "SELECT role, content, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp ASC",
            (self.chat_id,)
        )
        rows = self.cursor.fetchall()
        self.history = [
            {"role": role, "parts": [content], "timestamp": timestamp}
            for role, content, timestamp in rows
        ]

        # --- Load history for model context ---
        self.cursor.execute(
            "SELECT role, content FROM messages WHERE chat_id=? ORDER BY timestamp ASC",
            (self.chat_id,)
        )
        rows = self.cursor.fetchall()
        self.full_history = [
            {"role": role, "parts": [{"text": content}]}
            for role, content in rows
        ]

        # If no model set, pick a working one for the provider
        if not self.model_name:
            if self.provider_name == "gemini":
                # Lazy import to avoid loading tofetchmodal at module import
                from src.tofetchmodal import get_working_model as get_gemini_working_model
                self.model_name = get_gemini_working_model(self.persona)
            else:
                # For other providers, pick first from their list or None
                provider_temp = self.provider_class(self.config, self.persona)
                models = provider_temp.get_available_models()
                self.model_name = models[0] if models else None

    def _get_provider_class(self, provider_name: str) -> type:
        """Lazy load provider class to avoid importing all dependencies at startup."""
        if provider_name == "gemini":
            from src.providers.gemini import GeminiProvider
            return GeminiProvider
        elif provider_name == "openrouter":
            from src.providers.openrouter import OpenRouterProvider
            return OpenRouterProvider
        elif provider_name == "openai":
            from src.providers.openai import OpenAIProvider
            return OpenAIProvider
        elif provider_name == "anthropic":
            from src.providers.anthropic import AnthropicProvider
            return AnthropicProvider
        else:
            from src.providers.gemini import GeminiProvider
            return GeminiProvider

    def initialize_provider(self):
        """Initialize the selected provider with current config and history."""
        # Create provider instance
        self.provider = self.provider_class(self.config, self.persona)

        # Provide history to provider for context
        self.provider.full_history = self.full_history

        # Set model name if we have one
        if self.model_name:
            self.provider.model_name = self.model_name

        # Initialize the provider
        self.provider.initialize()

        # Sync model name from provider (might have fallback)
        self.model_name = self.provider.model_name

        # Delegate chat session to provider
        self.chat_session = self.provider.chat_session

    def is_model_loaded(self):
        """Check if provider is initialized and ready."""
        return self.provider is not None and self.provider.is_initialized()

    def get_available_models(self):
        """Return list of known working model names for the current provider."""
        if self.provider:
            return self.provider.get_available_models()
        return []

    def switch_model(self, new_model_name):
        """
        Switch to a different model using the provider.

        Returns:
            tuple: (success, error_message)
        """
        if not self.provider:
            return False, "Provider not initialized"
        success, error = self.provider.switch_model(new_model_name)
        if success:
            # Sync brain's model_name with provider's
            self.model_name = self.provider.model_name
            # Persist to config
            edit_config(model=self.model_name)
        return success, error

    def get_model_rank(self, model_name):
        """Get the index of a model in the priority list (0 = highest)."""
        if self.provider:
            return self.provider.get_model_rank(model_name)
        models = self.get_available_models()
        try:
            return models.index(model_name)
        except ValueError:
            return len(models)

    def find_better_model(self):
        """
        Check if there's a better (higher-ranked) model available.
        Returns the better model name if found, otherwise None.
        """
        if self.provider:
            return self.provider.find_better_model()
        return None

    def start_background_model_refresh(self, interval_hours=1):
        """
        Start background thread that periodically checks for better models.
        Runs every interval_hours while the chat is active.
        """
        import threading
        import time

        def refresh_loop():
            while True:
                time.sleep(interval_hours * 3600)
                better = self.find_better_model()
                if better:
                    success, error = self.switch_model(better)
                    # Could log this somewhere if needed

        thread = threading.Thread(target=refresh_loop, daemon=True)
        thread.start()
        return thread

    def choose_chat_db(self):
        """Fallback interactive chat selection (only used if not passed)."""
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

    def get_metadata(self):
        """Get current chat metadata for UI toolbar."""
        exchanges = len(self.history) // 2 if self.history else 0

        # Get last activity timestamp
        last_activity = None
        if self.history:
            last_msg = self.history[-1]
            ts = last_msg.get("timestamp")
            if ts:
                last_activity = self._format_time_display(ts)

        # Get model name from provider if available
        model_display = self.model_name if self.model_name else "loading..."

        return {
            "model": model_display,
            "chat_name": self.chat_name,
            "exchanges": exchanges,
            "timestamps_enabled": self.show_timestamps,
            "last_activity": last_activity
        }

    def _format_time_display(self, ts):
        """Format timestamp for display (HH:MM, local time)."""
        if not ts:
            return ""
        try:
            from datetime import datetime
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                dt = ts

            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                dt = dt.astimezone()

            return dt.strftime("%H:%M")
        except Exception:
            return str(ts)[:5] if isinstance(ts, str) else ""

    def get_history(self):
        """Return full history for rendering."""
        return self.history

    def send_message(self, user_input):
        """
        Send user message, get response, save to DB.

        Returns:
            tuple: (response_text, model_ts)
        """
        user_ts = datetime.now(timezone.utc)

        try:
            response_text = self.provider.send_message(user_input)
            model_ts = datetime.now(timezone.utc)

            # Save user message
            self.cursor.execute(
                "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.chat_id, "user", user_input, user_ts)
            )
            # Save model response
            self.cursor.execute(
                "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (self.chat_id, "model", response_text, model_ts)
            )
            self.conn.commit()

            # Append to in-memory history
            self.history.append({
                "role": "user",
                "parts": [user_input],
                "timestamp": user_ts
            })
            self.history.append({
                "role": "model",
                "parts": [response_text],
                "timestamp": model_ts
            })

            return response_text, model_ts

        except Exception as e:
            return f"[bold red]Error: Something went wrong: {e}[/bold red]", None

    def close(self):
        """Close database connection and clean up provider."""
        if self.provider:
            self.provider.close()
        self.conn.close()

    # --- Command handling (returns action dict or None) ---

    def handle_command(self, cmd_line):
        """
        Handle slash commands. Returns dict with action info or None.

        Commands: help, exit, save, copy, export, status, timestamp, animation, clear, model, refresh_model
        """
        parts = cmd_line.strip().split()
        cmd = parts[0].lower() if parts else ""
        args = parts[1:]

        if cmd == "help":
            return {"action": "help"}

        elif cmd == "exit":
            return {"action": "exit"}

        elif cmd == "save":
            import os, json
            os.makedirs("exports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"exports/{self.chat_name}_{timestamp}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False, default=str)
            return {"action": "message", "message": f"Chat saved to {fname}"}

        elif cmd == "copy":
            # Copy last AI response to clipboard
            for msg in reversed(self.history):
                if msg["role"] == "model":
                    text = "\n".join(msg["parts"]).strip()
                    try:
                        import pyperclip
                        pyperclip.copy(text)
                        return {"action": "message", "message": "Last response copied to clipboard."}
                    except ImportError:
                        return {"action": "message", "message": "pyperclip not installed. Install with: pip install pyperclip"}
            return {"action": "message", "message": "No AI response to copy yet."}

        elif cmd == "export":
            import os
            os.makedirs("exports", exist_ok=True)
            if args:
                fname = args[0]
                if not fname.endswith('.md'):
                    fname += '.md'
            else:
                fname = f"{self.chat_name}.md"
            path = os.path.join("exports", fname)
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# {self.chat_name}\n\n")
                for msg in self.history:
                    role = "You" if msg["role"] == "user" else "Nomi"
                    content = "\n".join(msg["parts"]).strip()
                    f.write(f"## {role}\n{content}\n\n")
            return {"action": "message", "message": f"Chat exported to {path}"}

        elif cmd == "status":
            exchanges = len(self.history) // 2
            token_est = sum(len(m["parts"][0].split()) for m in self.history if m["parts"])
            return {
                "action": "status",
                "data": {
                    "chat": self.chat_name,
                    "model": self.model_name,
                    "exchanges": exchanges,
                    "tokens": int(token_est),
                    "timestamps": self.show_timestamps
                }
            }

        elif cmd == "timestamp":
            current = self.show_timestamps
            self.show_timestamps = not current
            edit_config(ui={"show_timestamps": self.show_timestamps})
            return {"action": "message", "message": f"Timestamps {'enabled' if self.show_timestamps else 'disabled'}"}

        elif cmd == "animation":
            ui_cfg = self.config.get("ui", {})
            current = ui_cfg.get("animation_enabled", True)
            new_val = not current
            edit_config(ui={"animation_enabled": new_val})
            self.config["ui"]["animation_enabled"] = new_val
            return {"action": "message", "message": f"Animations {'enabled' if new_val else 'disabled'}"}

        elif cmd == "clear":
            return {"action": "clear"}

        elif cmd == "model":
            # Return list of available models for UI to display/select
            models = self.get_available_models()
            return {"action": "select_model", "models": models}

        elif cmd == "refresh_model":
            return {"action": "refresh_model"}

        else:
            return {"action": "message", "message": f"Unknown command: /{cmd}. Type /help for available commands."}
