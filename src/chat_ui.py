# Chat UI layer - handles all presentation

from rich.console import Console
from rich.markdown import Markdown
from rich.rule import Rule
from rich.panel import Panel
from src.utils.cli import get_user_input

class ChatRenderer:
    def __init__(self, console=None, code_theme=None):
        self.console = console or Console()
        # Apply code block styling
        if code_theme:
            self.console.push_theme(code_theme)

    def display_banner(self):
        """Display the NOMI banner (optional pre-chat)."""
        pass  # Handled by menu layer

    def render_message(self, role, content, timestamp=None, show_timestamp=True):
        """Render a single message."""
        # Show timestamp if enabled and provided
        if show_timestamp and timestamp:
            ts = self._format_timestamp(timestamp)
            if ts:
                self.console.print(f"[dim]{ts}[/dim]", justify="right")

        if role == "user":
            self.console.print(f"[bold #b4befe]You:[/] {content}")
        elif role == "model":
            self.console.print(f"[bold green]Nomi:[/]", end=" ")
            self.console.print(Markdown(content))
        self.console.print("")

    def render_separator(self):
        """Render a horizontal separator between exchanges."""
        self.console.print(Rule(style="dim", characters="─"))

    def render_blank_line(self):
        """Print a blank line."""
        self.console.print()

    def get_input(self, chat_info):
        """Get user input with toolbar."""
        return get_user_input(chat_info=chat_info)

    def show_status(self, message):
        """Show a status message (e.g., loading)."""
        self.console.print(f"[dim]{message}[/dim]")

    def show_error(self, error):
        """Show an error message."""
        self.console.print(f"[bold red]Error: {error}[/bold red]")

    def _format_timestamp(self, ts):
        """Format a timestamp for display."""
        if not ts:
            return ""
        try:
            from datetime import datetime
            # Parse to datetime
            if isinstance(ts, str):
                dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            else:
                dt = ts

            # Convert to local time if timezone-aware
            if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
                dt = dt.astimezone()  # Convert to system local timezone

            # Show time if today, date+time if older
            today = datetime.now().date()
            if dt.date() == today:
                return dt.strftime("%H:%M")
            else:
                return dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            return str(ts)[:16] if isinstance(ts, str) else ""
