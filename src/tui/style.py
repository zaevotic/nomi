"""
Retro ASCII theme for Nomi TUI.
Colors are configurable via config.yaml under `ui.colors`.
"""

DEFAULT_RETRO_COLORS = {
    "fg": "#c0c0c0",          # Light gray default text
    "bg": "#000000",          # Black background
    "accent": "#ffb000",      # Amber
    "border": "#00ff00",      # Green (retro terminal)
    "panel": "#1a1a1a",       # Dark gray for panels
    "user_msg": "#00ffff",    # Cyan for user messages
    "nomi_msg": "#00ff00",    # Green for Nomi messages
    "dim": "#666666",         # Dim gray for timestamps/meta
    "error": "#ff5555",       # Red for errors
}

def get_retro_colors(config: dict) -> dict:
    ui_colors = config.get("ui", {}).get("colors", {})
    colors = DEFAULT_RETRO_COLORS.copy()
    colors.update(ui_colors)
    return colors
