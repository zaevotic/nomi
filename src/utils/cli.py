from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

def prompt_continuation(width, line_number, wrap_count):
    if wrap_count > 0:
        return " " * (width - 3) + "→ "
    else:
        text = ("- %i - " % (line_number + 1)).rjust(width)
        return HTML("<line-number>%s</line-number>" % text)

kb = KeyBindings()

@kb.add("c-m")
def _(event):
    """Submit"""
    buffer = event.current_buffer
    if buffer.validate():
        buffer.validate_and_handle()

@kb.add("c-\\")
def _(event):
    """Insert newline"""
    event.current_buffer.insert_text("\n")

# Custom style
custom_style = Style.from_dict({
    "prompt": "bold #b4befe",
    "line-number": "#b4befe",
})

session = PromptSession(key_bindings=kb, style=custom_style)

def get_user_input(chat_info=None):
    """
    Get user input with optional status bar below input.

    Args:
        chat_info: dict with keys: model, chat_name, exchanges, last_activity, timestamps_enabled
    """
    if not chat_info:
        # Simple mode - just get input
        return session.prompt(
            HTML("<prompt><b>You:</b></prompt> "),
            multiline=True,
            prompt_continuation=prompt_continuation
        )

    # Build status string
    model = chat_info.get("model", "")
    chat_name = chat_info.get("chat_name", "")
    exchanges = chat_info.get("exchanges", 0)
    last_activity = chat_info.get("last_activity")
    ts_enabled = chat_info.get("timestamps_enabled", True)

    parts = []
    if model:
        parts.append(f"Model: {model}")
    if chat_name:
        parts.append(f"Chat: {chat_name}")
    if exchanges is not None:
        parts.append(f"Msgs: {exchanges}")
    if last_activity:
        parts.append(f"Last: {last_activity}")

    status = " | ".join(parts)
    if ts_enabled:
        status += " (ts: on)"
    else:
        status += " (ts: off)"

    # Create a bottom toolbar that looks like a status pane
    def get_toolbar():
        return status

    return session.prompt(
        HTML("<prompt><b>You:</b></prompt> "),
        multiline=True,
        prompt_continuation=prompt_continuation,
        bottom_toolbar=get_toolbar
    )
