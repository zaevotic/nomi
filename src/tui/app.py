#!/usr/bin/env python3
"""Minimal TUI - single pane with 2px border"""

import sys
import os
from pathlib import Path
import sqlite3
import asyncio
from datetime import datetime, timezone
from textual.app import App, ComposeResult
from textual.widgets import Static, ListView, ListItem, Label, RichLog, Input, TextArea, Markdown
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.message import Message
from src.tui.style import get_retro_colors
from src.brain import Brain
from src import menu

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# ========== Chat List Components ==========

class ChatListItem(ListItem):
    """A chat list item with name and metadata."""
    def __init__(self, chat_id: int, chat_name: str, snippet: str = "", msg_count: int = 0, last_active: str = ""):
        super().__init__()
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.snippet = snippet
        self.msg_count = msg_count
        self.last_active = last_active

    def compose(self) -> ComposeResult:
        meta = f"{self.msg_count} msgs • {self.last_active}"
        yield Label(f"[bold]{self.chat_name}[/bold]", classes="chat-name")
        if self.snippet:
            yield Label(f"[dim]{self.snippet}[/dim]", classes="chat-snippet")
        yield Label(f"[cyan]{meta}[/cyan]", classes="chat-meta")

class ChatListView(Vertical):
    """Left pane: list of chats."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chats = []

    def compose(self) -> ComposeResult:
        yield Static("[bold]Chats[/bold]", classes="pane-title")
        yield ListView(id="chat-list-view")

    def load_chats(self):
        list_view = self.query_one(ListView)
        list_view.clear()
        # Add "+ New Chat" item at top
        new_chat_item = ListItem(Label("+ New Chat"), id="new-chat-item")
        list_view.append(new_chat_item)
        # Load existing chats from database
        try:
            conn = sqlite3.connect("nomi_memory.db")
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.id, c.name,
                       COUNT(m.id) as msg_count,
                       MAX(m.timestamp) as last_active,
                       (SELECT content FROM messages WHERE chat_id=c.id ORDER BY timestamp DESC LIMIT 1) as snippet
                FROM chats c
                LEFT JOIN messages m ON c.id = m.chat_id
                GROUP BY c.id
                ORDER BY last_active DESC NULLS LAST
            """)
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                chat_id, name, msg_count, last_active, snippet = row
                # Format snippet
                snippet_display = ""
                if snippet:
                    snippet_clean = snippet.replace("\n", " ").strip()
                    if len(snippet_clean) > 50:
                        snippet_display = snippet_clean[:47] + "..."
                    else:
                        snippet_display = snippet_clean
                # Format last_active time
                active_str = ""
                if last_active:
                    try:
                        if isinstance(last_active, str):
                            dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                        else:
                            dt = last_active
                        active_str = dt.strftime("%H:%M" if dt.date() == datetime.now().date() else "%m-%d %H:%M")
                    except Exception:
                        active_str = str(last_active)[:16]
                item = ChatListItem(chat_id, name, snippet_display, msg_count or 0, active_str)
                list_view.append(item)
        except Exception as e:
            # If database doesn't exist or table missing, that's ok for now
            pass

class MessageSubmitted(Message):
    """Message sent when user submits input."""
    def __init__(self, text: str):
        super().__init__()
        self.text = text

# ========== Conversation View ==========

class ConversationView(Vertical):
    """Top-right pane: conversation messages display only."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_chat_id = None

    def compose(self) -> ComposeResult:
        yield Static("[bold]Conversation[/bold]", classes="pane-title")
        yield ScrollableContainer(id="messages-container")

    def show_chat(self, chat_id: int):
        """Load and display messages for a chat."""
        self.current_chat_id = chat_id
        container = self.query_one("#messages-container", ScrollableContainer)
        container.remove_children()
        try:
            conn = sqlite3.connect("nomi_memory.db")
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role, content, timestamp FROM messages WHERE chat_id=? ORDER BY timestamp ASC",
                (chat_id,)
            )
            rows = cursor.fetchall()
            conn.close()

            for role, content, ts in rows:
                self._add_message(role, content, ts)
            container.scroll_end(animate=False)
        except Exception as e:
            error_md = Markdown(f"**Error:** `{e}`")
            container.mount(error_md)

    def _add_message(self, role: str, content: str, ts):
        """Add a message to the conversation view with markdown rendering."""
        container = self.query_one("#messages-container", ScrollableContainer)
        # Determine colors
        user_color = self.app.retro_colors.get("user_msg", "#00ffff") if hasattr(self.app, 'retro_colors') else "#00ffff"
        nomi_color = self.app.retro_colors.get("nomi_msg", "#00ff00") if hasattr(self.app, 'retro_colors') else "#00ff00"
        # Format timestamp
        try:
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                dt = ts
            ts_str = dt.strftime("%H:%M")
        except Exception:
            ts_str = ""
        # Role display and color
        role_display = "You" if role == "user" else "Nomi"
        color = user_color if role == "user" else nomi_color
        # Build markdown with CSS classes for colors
        role_class = "user-msg" if role == "user" else "nomi-msg"
        md_text = f'<span class="ts">{ts_str}</span> <b class="{role_class}">{role_display}:</b>\n\n{content}'
        # Create Markdown widget
        md_widget = Markdown(md_text, classes="message")
        container.mount(md_widget)
        # Separator line
        separator = Static("──────────────────────────────────────────────────", classes="separator")
        container.mount(separator)
        container.scroll_end(animate=False)

# ========== Input Animation View ==========

class SubmitTextArea(TextArea):
    """TextArea for chat input. Enter = send, Shift+Enter = newline, '/' triggers command mode."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._in_command_mode = False
        self._command_callback = None

    def on_key(self, event) -> None:
        # Check if we're in command mode
        if self._in_command_mode:
            if event.key == "enter":
                # Execute the command
                command = self.text.strip()
                if command:
                    self._execute_command(command)
                self._exit_command_mode()
                event.stop()
                event.prevent_default()
                return
            elif event.key == "escape":
                # Cancel command mode
                self._exit_command_mode()
                event.stop()
                return
            # In command mode, other keys are handled normally (building the command)
            # We'll still let TextArea process them
            return

        # Normal mode
        if event.key == "enter":
            # Check if Shift is pressed using getattr with fallback
            shift = getattr(event, 'shift', False) or getattr(event, 'shift_key', False)
            if shift:
                # Shift+Enter = newline (let TextArea handle it)
                return
            else:
                # Enter without Shift = send message
                text = self.text.strip()
                if text:
                    self.post_message(MessageSubmitted(text))
                    self.text = ""
                event.stop()
                event.prevent_default()
                return
        # '/' triggers command mode
        if event.key == "/":
            event.stop()
            self._start_command_mode()
            return
        # All other keys: let TextArea handle normally

    def _start_command_mode(self):
        """Activate command mode - intercepts / for commands."""
        self._in_command_mode = True
        # Save current text for restoration after command
        self._saved_text = self.text
        self.text = "/"
        # Move cursor to end
        self.move_cursor(self.document.end)
        # Visual feedback: change border color to indicate command mode
        try:
            self.styles.border = ("solid", "#ffff00")  # Yellow border
        except:
            pass
        # Log to console
        if hasattr(self.app, '_log_to_console'):
            self.app._log_to_console("Command mode: type a command (Esc to cancel)", "info")

    def _execute_command(self, command: str):
        """Execute a command. Placeholder for future command system."""
        # Log the command that was executed
        if hasattr(self.app, '_log_to_console'):
            self.app._log_to_console(f"Executing command: {command}", "warning")
        # For now, just echo back - later you'll add actual command handlers
        # Could also integrate with the log header or show a modal

    def _exit_command_mode(self):
        """Exit command mode and restore normal state."""
        self._in_command_mode = False
        # Remove visual feedback
        try:
            self.styles.border = ("solid", None)  # Reset to default
        except:
            pass
        # Restore previous text (if any)
        if hasattr(self, '_saved_text'):
            self.text = self._saved_text
            self._saved_text = ""
        else:
            self.text = ""

class InputAnimationView(Vertical):
    """Bottom-left pane: input area (and future animations)."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Static("[bold]Input[/bold]", classes="pane-title")
        with Vertical(id="input-area"):
            yield SubmitTextArea(id="msg-input", show_line_numbers=False, soft_wrap=True)
            yield Static("Chars: 0/4000", id="char-count")
            yield Static("Enter: Send  •  Shift+Enter: New line  •  /: Commands", id="input-hint", classes="input-hint")

    def on_message_submitted(self, message: MessageSubmitted):
        """Clear the input and update char count after submission."""
        # Text cleared by SubmitTextArea, just reset char count
        self.query_one("#char-count", Static).update("Chars: 0/4000")

    def on_text_area_changed(self, event: TextArea.Changed):
        text = event.text_area.text.strip()
        count = len(text)
        self.query_one("#char-count", Static).update(f"Chars: {count}/4000")

# ========== Log Console View ==========

class LogConsoleView(Vertical):
    """Bottom-right pane: activity log and console with info header."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.header_chat = "No chat selected"
        self.header_model = ""

    def compose(self) -> ComposeResult:
        # Info header showing current chat and model with live time
        yield Static("", id="log-header", classes="log-header")
        yield RichLog(id="console-log", markup=True)

    def on_mount(self):
        """Start a timer to update the time in the header every second."""
        self.set_interval(1.0, self._update_time)

    def _update_time(self):
        """Update the time portion of the header."""
        time_str = datetime.now().strftime("%H:%M:%S")
        text = f"Chat: {self.header_chat}"
        if self.header_model:
            text += f" | Model: {self.header_model}"
        text += f" | Time: {time_str}"
        try:
            self.query_one("#log-header", Static).update(text)
        except Exception:
            pass

    def update_info(self, chat_name: str, model_name: str = ""):
        """Update the header with current chat and model info."""
        self.header_chat = chat_name or "No chat selected"
        self.header_model = model_name or ""
        # Immediately update the display with current time
        self._update_time()

    def log(self, message: str, level: str = "info"):
        """Write a colored log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        # Color based on level
        colors = {
            "info": "cyan",
            "error": "red",
            "warning": "yellow",
            "debug": "dim"
        }
        color = colors.get(level, "white")
        formatted = f"[dim]{timestamp}[/dim] [{color}]{level.upper():<7}[/{color}] {message}"
        try:
            self.query_one("#console-log", RichLog).write(formatted)
        except Exception as e:
            print(f"[LOG ERROR] {e}", file=sys.stderr)

# ========== Main App ==========

class MinimalApp(App):
    """Test app with chat list."""

    def __init__(self):
        super().__init__()
        self.retro_colors = get_retro_colors({})
        self.current_chat_id = None
        self.current_chat_name = None
        self.current_model_name = None
        self.brains = {}  # chat_id -> Brain instance
        self.config = menu.get_config()
        # Disable Brain's console animations/spinner to avoid terminal interference
        self.config.setdefault("ui", {})["animation_enabled"] = False

    CSS = """
Screen {
    layout: vertical;
}
/* Main container with horizontal layout */
#main-container {
    layout: horizontal;
    width: 100%;
    height: 1fr;
}
/* Left pane - 20% (1fr out of 5 total) */
.left {
    width: 1fr;
    min-width: 0;
    min-height: 0;
    border: solid green;
}
.left > ListView {
    height: 1fr;
}
/* Chat list items - truncate text with ellipsis */
.chat-name, .chat-snippet, .chat-meta {
    width: 100%;
    text-overflow: ellipsis;
    overflow: hidden;
}
/* Pane title styling */
.pane-title {
    background: #008000;  /* Green */
    color: white;
    padding: 0 1;
    text-style: bold;
    height: 1;
    width: 100%;
    margin: 0;
}
/* Right pane - 80% (4fr out of 5 total) */
.right {
    width: 4fr;
    min-width: 0;
    min-height: 0;
    layout: vertical;
}
/* Right top - 70% of right (7fr out of 10 total) */
.right-top {
    height: 7fr;
    border: solid yellow;
    layout: vertical;
}
.right-top > .pane-title {
    background: #808000;  /* Olive */
}
/* Messages container */
#messages-container {
    height: 1fr;
}
.message {
    margin: 0 0;
    padding: 0 1;
    width: 100%;
}
.message > * {
    width: 100%;
}
/* Message styling via classes */
.ts {
    color: #666;
}
.user-msg {
    color: #00ffff;
}
.nomi-msg {
    color: #00ff00;
}
/* Separator between messages */
.separator {
    margin: 0;
    padding: 0;
    color: #666;
    height: 1;
    width: 100%;
    text-align: center;
}
/* Right bottom - 30% of right (3fr out of 10 total) */
.right-bottom {
    height: 3fr;
    min-height: 0;
    layout: horizontal;
}
/* Bottom left - 50% (1fr out of 2) */
.right-bottom-left {
    width: 1fr;
    min-width: 0;
    min-height: 0;
    border: solid cyan;
}
/* Bottom right - 50% (1fr out of 2) */
.right-bottom-right {
    width: 1fr;
    min-width: 0;
    min-height: 0;
    border: solid red;
}
/* Input area inside InputAnimationView */
#input-area {
    layout: vertical;
    height: 1fr;
}
#msg-input {
    height: 1fr;
    border: none;
}
#char-count {
    text-align: right;
    color: white;
    background: #008000;
    height: 1;
    width: 100%;
}
/* Input hint bar */
.input-hint {
    color: #888;
    text-align: center;
    height: 1;
    width: 100%;
    background: #222;
}
/* Console log inside LogConsoleView */
#console-log {
    height: 1fr;
}
/* Log header info bar */
.log-header {
    color: #00ff00;
    padding: 0 1;
    height: 1;
    width: 100%;
    text-align: left;
    background: #004400;
}
"""

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-container"):
            # Left: ChatListView (20% width)
            yield ChatListView(classes="left")
            # Right: 80% width, vertical layout
            with Vertical(classes="right"):
                yield ConversationView(classes="right-top")
                # Bottom: horizontal split (30% of right)
                with Horizontal(classes="right-bottom"):
                    yield InputAnimationView(classes="right-bottom-left")
                    yield LogConsoleView(classes="right-bottom-right")

    def on_mount(self):
        # Ensure database exists and schema is current
        if not os.path.exists("nomi_memory.db"):
            conn = sqlite3.connect("nomi_memory.db")
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (chat_id) REFERENCES chats (id)
                )
            """)
            conn.commit()
            conn.close()
        # Apply migrations (add meta column if missing)
        conn = sqlite3.connect("nomi_memory.db")
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN meta JSON")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.commit()
        conn.close()

        # Load chats after UI is ready
        chat_list = self.query_one(ChatListView)
        chat_list.load_chats()
        # Set initial focus on chat list
        chat_list.focus()
        # Initialize log header with current state
        self._update_log_info()

    def on_list_view_selected(self, event: ListView.Selected):
        """Handle chat selection."""
        if event.list_view.id == "chat-list-view":
            item = event.item
            if item and item.id == "new-chat-item":
                self._log_to_console("Create new chat (not implemented)", "info")
            elif isinstance(item, ChatListItem):
                self.switch_chat(item.chat_id, item.chat_name)

    def switch_chat(self, chat_id: int, chat_name: str):
        """Switch to a different chat."""
        self.current_chat_id = chat_id
        self.current_chat_name = chat_name
        # Check if we already have a Brain for this chat to get its model
        brain = self.brains.get(chat_id)
        if brain is not None:
            self.current_model_name = brain.model_name
        else:
            self.current_model_name = None
        self._update_log_info()
        conversation_view = self.query_one(ConversationView)
        conversation_view.show_chat(chat_id)
        try:
            self.query_one("#msg-input", TextArea).focus()
        except Exception:
            pass
        self._log_to_console(f"Switched to chat: {chat_name}", "info")

    def _log_to_console(self, message: str, level: str = "info"):
        """Log messages from Brain to the LogConsoleView (thread-safe)."""
        def do_log():
            try:
                log_view = self.query_one(LogConsoleView)
                log_view.log(message, level)
            except Exception as e:
                # Fallback to stderr if UI not ready
                import sys
                print(f"[{level.upper()}] {message}", file=sys.stderr)
        # call_from_thread is available even after app is running
        try:
            self.call_from_thread(do_log)
        except Exception:
            # If app is not running or something, just ignore
            pass

    def _update_log_info(self):
        """Update the LogConsoleView header with current chat and model info."""
        try:
            log_view = self.query_one(LogConsoleView)
            chat_name = self.current_chat_name or "No chat selected"
            model_name = self.current_model_name or ""
            log_view.update_info(chat_name, model_name)
        except Exception:
            pass

    def _get_brain_for_chat(self, chat_id, chat_name):
        """Get or create a Brain instance for the given chat."""
        brain = self.brains.get(chat_id)
        if brain is None:
            try:
                brain = Brain(
                    config=self.config,
                    chat_id=chat_id,
                    chat_name=chat_name,
                    log_callback=self._log_to_console
                )
                self.brains[chat_id] = brain
                # Update current model name from the new brain
                self.current_model_name = brain.model_name
                self._update_log_info()
            except Exception as e:
                import traceback
                tb = traceback.format_exc()
                self._log_to_console(f"Brain init failed for chat {chat_id}:\n{e}\n{tb}", "error")
                return None
        return brain

    async def on_message_submitted(self, message: MessageSubmitted):
        """Handle sent messages with Brain integration."""
        if not self.current_chat_id:
            self._log_to_console("No chat selected!", "error")
            return
        conversation_view = self.query_one(ConversationView)
        # User timestamp (UTC)
        user_ts = datetime.now(timezone.utc)
        # Get or create Brain for this chat
        brain = self._get_brain_for_chat(self.current_chat_id, self.current_chat_name)
        if brain is None:
            # Error already logged by _get_brain_for_chat
            return
        # Add user message to UI immediately
        conversation_view._add_message("user", message.text, user_ts)
        # Generate Nomi response in a thread to avoid blocking UI
        try:
            response_text, model_ts = await asyncio.to_thread(brain.generate_response, message.text, user_ts)
            # Add Nomi response to UI
            if model_ts is None:
                model_ts = datetime.now(timezone.utc)
            conversation_view._add_message("nomi", response_text, model_ts)
        except Exception as e:
            conversation_view._add_message("nomi", f"Error: {e}", datetime.now(timezone.utc))
            self._log_to_console(f"Error generating response: {e}", "error")


if __name__ == "__main__":
    app = MinimalApp()
    app.run()
