from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.validation import Validator, ValidationError

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

def get_user_input(char_limit=None):
    """
    Get user input with optional character count toolbar.

    Args:
        char_limit: Maximum allowed characters. If exceeded, toolbar shows warning.
                    If None, no toolbar is shown.
    """
    bottom_toolbar = None
    if char_limit is not None:
        def get_toolbar():
            buf = session.app.current_buffer
            text = buf.text
            count = len(text)
            # Show count as "123/4000", bold if over limit
            if count > char_limit:
                return HTML("<b>Chars: {}/{}</b>".format(count, char_limit))
            else:
                return "Chars: {}/{}".format(count, char_limit)
        bottom_toolbar = get_toolbar

    return session.prompt(
        HTML("<prompt><b>You:</b></prompt> "),
        multiline=True,
        prompt_continuation=prompt_continuation,
        bottom_toolbar=bottom_toolbar
    )

