#loading menu trial

import os
import time
import warnings
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Disable questionary styling warnings (must be before importing questionary)
os.environ['QUESTIONARY_DISABLE_STYLES'] = '1'
os.environ['QUESTIONARY_NO_STYLE'] = '1'
os.environ['QUESTIONARY_USE_ANSI_COLORS'] = '1'
os.environ['QUESTIONARY_STYLE'] = 'none'  # Force no style
os.environ['PYTHONWARNINGS'] = 'ignore'  # Suppress all warnings

# Suppress the specific warning about window_padding_height from prompt_toolkit
warnings.filterwarnings("ignore", message="Ignoring unknown config key")

import sqlite3, yaml, questionary, platform, importlib
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from questionary import Choice
from prompt_toolkit.styles import Style

# Custom style for questionary prompts
custom_style = Style.from_dict({
    "prompt": "bold #b4befe",
    "line-number": "#b4befe",
})

# Special style for destructive/exit choices
exit_choice_style = Style.from_dict({
    "choice": "bold red",
    "choice-selected": "bold red bg:#444444",
})

# Plugin system
PLUGINS = []

# Main banner - shown on all menu screens
BANNER = r"""
[bold magenta]
  b.             8     ,o888888o.           ,8.       ,8.           8 8888
  888o.          8  . 8888     `88.        ,888.     ,888.          8 8888
  Y88888o.       8 ,8 8888       `8b      .`8888.   .`8888.         8 8888
  .`Y888888o.    8 88 8888        `8b    ,8.`8888. ,8.`8888.        8 8888
  8o. `Y888888o. 8 88 8888         88   ,8'8.`8888,8^8.`8888.       8 8888
  8`Y8o. `Y88888o8 88 8888         88  ,8' `8.`8888' `8.`8888.      8 8888
  8   `Y8o. `Y8888 88 8888        ,8P ,8'   `8.`88'   `8.`8888.     8 8888
  8      `Y8o. `Y8 `8 8888       ,8P ,8'     `8.`'     `8.`8888.    8 8888
  8         `Y8o.`  ` 8888     ,88' ,8'       `8        `8.`8888.   8 8888
  8            `Yo     `8888888P'  ,8'         `         `8.`8888.  8 8888
[/]
[bold cyan]          Your AI Companion with Memory & Personality[/]

[dim]───────────────────────────────────────────────────────────[/]
"""

def discover_plugins():
    """Discover and load plugin modules from the plugins directory."""
    global PLUGINS
    PLUGINS = []  # reset
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    if not os.path.exists(plugins_dir):
        return
    for filename in os.listdir(plugins_dir):
        if filename.endswith(".py") and not filename.startswith("_"):
            module_name = filename[:-3]
            filepath = os.path.join(plugins_dir, filename)
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(module)
                    if hasattr(module, "plugin_menu"):
                        label, handler = module.plugin_menu()
                        PLUGINS.append((label, handler))
                except Exception as e:
                    console.print(f"[red]Failed to load plugin {module_name}: {e}[/]")

CONFIG_PATH = "config.yaml"


console = Console()
# chat_dir = "chats"
DB_NAME = "nomi_memory.db"

def get_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg = yaml.safe_load(f) or {}
            # Ensure UI section exists with defaults
        if "ui" not in cfg:
            cfg["ui"] = {
                "show_timestamps": True,
                "animation_enabled": True,
                "character_limit": 4000,
                "mode": "cli",
            }
        else:
            if "show_timestamps" not in cfg["ui"]:
                cfg["ui"]["show_timestamps"] = True
            if "animation_enabled" not in cfg["ui"]:
                cfg["ui"]["animation_enabled"] = True
            if "character_limit" not in cfg["ui"]:
                cfg["ui"]["character_limit"] = 4000
            if "mode" not in cfg["ui"]:
                cfg["ui"]["mode"] = "cli"
        # Ensure provider and api_keys exist
        if "provider" not in cfg:
            cfg["provider"] = "gemini"
        if "api_keys" not in cfg:
            cfg["api_keys"] = {}
        return cfg
    except FileNotFoundError:
        # Create default config if it doesn't exist
        default_config = {
            "default_model": "gemini-1.5-flash",
            "provider": "gemini",
            "persona": "",
            "ui": {
                "show_timestamps": True,
                "animation_enabled": True,
                "character_limit": 4000,
                "mode": "cli",
            },
            "api_keys": {}
        }
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(default_config, f)
        return default_config

def center(text):
    return Align.center(Panel(text, expand=False))


def clear_console():
    system = platform.system().lower()
    if system == "linux" or system == "darwin":
        os.system('clear')
    elif system == "windows":
        os.system('cls')


    
def edit_config(model=None, persona=None, terminal=None, ui=None, provider=None, api_keys=None):
    # with open(CONFIG_PATH, "r") as f:
    #     cfg = yaml.safe_load(f)
    cfg = get_config()
    # if model: cfg["default_model"] = model
    if model is not None: cfg["default_model"] = model
    if persona is not None: cfg["persona"] = persona
    # if terminal: cfg["default_terminal"] = terminal
    if provider is not None: cfg["provider"] = provider
    if ui is not None:
        cfg["ui"].update(ui)
    if api_keys is not None:
        if "api_keys" not in cfg:
            cfg["api_keys"] = {}
        cfg["api_keys"].update(api_keys)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(cfg, f)

# def choose_model():
#     model = questionary.select(
#         "Pick a Gemini model:",
#         choices = [f"{m} - {desc}" for m, desc in MODELS.items()
#         ],
#         qmark=" ❯ "
#     ).ask()
#     return model.split(" ")[0]

def edit_persona():
    clear_console()
    console.print(BANNER)
    console.print("[bold #b4befe]  Edit Nomi's Persona[/]\n")

    with open(CONFIG_PATH, "r") as f:
        persona = yaml.safe_load(f).get("persona", "")

    # Show current persona in a panel if it exists
    if persona and persona.strip():
        console.print(Panel(persona, title="[bold]Current Persona[/]", border_style="green"))
        console.print("")

    new_p = questionary.text(
        "Enter new persona description (leave blank to keep current):",
        default=persona,
        multiline=True,
        qmark="✎"
    ).ask()

    clear_console()
    console.print(BANNER)
    console.print("[bold #b4befe]  Edit Nomi's Persona[/]\n")

    if new_p and new_p.strip() and new_p != persona:
        console.print(Panel(new_p, title="[bold green]Updated Persona[/]", border_style="green"))
        return new_p
    else:
        console.print("[yellow]No changes made to persona.[/]")
        return None

def edit_ui_settings():
    """Interactive UI settings editor."""
    while True:
        clear_console()
        console.print(BANNER)

        cfg = get_config()
        ui_cfg = cfg.get("ui", {})

        # Show current settings summary in a panel
        settings_text = ""
        settings_text += f"[cyan]Timestamps:[/]           [{ 'green' if ui_cfg.get('show_timestamps', True) else 'red' }]{ui_cfg.get('show_timestamps', True)}[/]\n"
        settings_text += f"[cyan]Animations:[/]           [{ 'green' if ui_cfg.get('animation_enabled', True) else 'red' }]{ui_cfg.get('animation_enabled', True)}[/]\n"
        settings_text += f"[cyan]Character Limit:[/]      [yellow]{ui_cfg.get('character_limit', 4000)}[/]\n"
        settings_text += f"[cyan]UI Mode:[/]              [yellow]{ui_cfg.get('mode', 'cli').upper()}[/]"

        console.print(Panel(settings_text, title="[bold]Current Settings[/]", border_style="blue"))
        console.print("")

        choice = questionary.select(
            "What would you like to change?",
            choices=[
                Choice(title="Toggle Timestamps", description="Show/hide message timestamps", value="Toggle Timestamps"),
                Choice(title="Toggle Animations", description="Enable/disable loading spinner", value="Toggle Animations"),
                Choice(title="Set Character Limit", description="Change maximum input length", value="Set Character Limit"),
                Choice(title="UI Mode", description="Switch between CLI and TUI", value="UI Mode"),
                Choice(title="Back", description="Return to main menu", value="Back")
            ],
            qmark="▶",
            style=custom_style
        ).ask()

        if choice == "Back" or choice is None:
            break

        elif choice == "Toggle Timestamps":
            current = ui_cfg.get("show_timestamps", True)
            new_val = questionary.confirm(
                f"Show timestamps on messages? (currently: {current})",
                default=not current  # Flip for suggestion
            ).ask()
            if new_val is not None:
                edit_config(ui={"show_timestamps": new_val})
                console.print(f"[green]Timestamps {'enabled' if new_val else 'disabled'}[/]")

        elif choice == "Toggle Animations":
            current = ui_cfg.get("animation_enabled", True)
            new_val = questionary.confirm(
                f"Enable animations? (currently: {current})",
                default=not current
            ).ask()
            if new_val is not None:
                edit_config(ui={"animation_enabled": new_val})
                console.print(f"[green]Animations {'enabled' if new_val else 'disabled'}[/]")

        elif choice == "Set Character Limit":
            current = ui_cfg.get("character_limit", 4000)
            new_val = questionary.text(
                f"Character limit for input (current: {current}):",
                default=str(current)
            ).ask()
            if new_val and new_val.isdigit():
                edit_config(ui={"character_limit": int(new_val)})
                console.print(f"[green]Character limit set to {int(new_val)}[/]")
            else:
                console.print("[red]Invalid number, keeping current value.[/]")

        elif choice == "UI Mode":
            current = ui_cfg.get("mode", "cli")
            console.print(f"\n[cyan]Current UI mode:[/] [bold]{current.upper()}[/]")
            new_mode = questionary.select(
                "Select UI mode:",
                choices=[
                    Choice(title="CLI", description="Classic command-line interface", value="cli"),
                    Choice(title="TUI", description="Modern Textual terminal UI", value="tui")
                ],
                qmark="▶",
                style=custom_style
            ).ask()
            if new_mode and new_mode != current:
                # Check if Textual is available for TUI
                if new_mode == "tui":
                    try:
                        import textual
                    except ImportError:
                        console.print("[red]Textual is not installed.[/]")
                        console.print("[yellow]Install it with: pip install textual[/]")
                        console.input("\n[dim]Press Enter to continue...[/]")
                        return None
                edit_config(ui={"mode": new_mode})
                console.print(f"[green]UI mode set to {new_mode.upper()}[/]")
                console.print("[yellow]Note: Change takes effect on next chat session.[/]")
                time.sleep(1)

def settings_menu():
    """Settings submenu - all configuration in one place."""
    while True:
        clear_console()
        console.print(BANNER)

        choice = questionary.select(
            "Settings:",
            choices=[
                Choice(
                    title="Edit Persona",
                    description="Customize Nomi's personality and behavior",
                    value="Edit Persona"
                ),
                Choice(
                    title="Appearance",
                    description="Timestamps, animations, character limit",
                    value="Appearance"
                ),
                Choice(
                    title="Model Selection",
                    description="Choose AI model and provider",
                    value="Model Selection"
                ),
                Choice(
                    title="API Configuration",
                    description="Set API keys and provider endpoints",
                    value="API Configuration"
                ),
                Choice(
                    title="Plugins",
                    description="View and manage installed plugins",
                    value="Plugins"
                ),
                Choice(
                    title="Back",
                    description="Return to main menu",
                    value="Back"
                )
            ],
            qmark="▶",
            style=custom_style
        ).ask()

        if choice == "Back" or choice is None:
            break

        elif choice == "Edit Persona":
            new_persona = edit_persona()
            if new_persona is not None:
                edit_config(persona=new_persona)

        elif choice == "Appearance":
            edit_ui_settings()

        elif choice == "Model Selection":
            _model_selection_menu()

        elif choice == "API Configuration":
            _api_config_menu()

        elif choice == "Plugins":
            show_plugins()

def _model_selection_menu():
    """Model & provider selection - pick a live provider, then search/select a model."""
    while True:
        clear_console()
        console.print(BANNER)

        cfg = get_config()
        current_model = cfg.get("default_model", "Not set")
        current_provider = cfg.get("provider", "gemini")

        console.print(Panel(
            f"[cyan]Provider:[/] [bold]{current_provider}[/]   "
            f"[cyan]Model:[/] [bold]{current_model}[/]",
            title="Current Selection",
            border_style="blue"
        ))
        console.print("")

        # Only show providers that are actually implemented.
        # Stubs (openrouter / openai / anthropic) are listed as info-only.
        provider_choice = questionary.select(
            "Step 1 — Select a provider:",
            choices=[
                Choice(
                    title=(
                        [("fg:ansigreen bold", "\u25cf"), ("", " Gemini (Google)")]
                        if current_provider == "gemini"
                        else "  Gemini (Google)"
                    ),
                    description="Google Gemini models — requires GEMINI_API_KEY",
                    value="gemini"
                ),
                Choice(
                    title=(
                        [("fg:ansigreen bold", "\u25cf"), ("", " Local (Ollama)")]
                        if current_provider == "local"
                        else "  Local (Ollama)"
                    ),
                    description="Locally running models via Ollama — no API key required",
                    value="local"
                ),
                Choice(
                    title="  OpenRouter  (coming soon)",
                    description="Not yet implemented",
                    value="_coming_soon"
                ),
                Choice(
                    title="  OpenAI  (coming soon)",
                    description="Not yet implemented",
                    value="_coming_soon"
                ),
                Choice(
                    title="  Anthropic  (coming soon)",
                    description="Not yet implemented",
                    value="_coming_soon"
                ),
                Choice(
                    title="Back",
                    description="Return to settings",
                    value="Back"
                ),
            ],
            qmark="▶",
            style=custom_style
        ).ask()

        if provider_choice == "Back" or provider_choice is None:
            break

        if provider_choice == "_coming_soon":
            console.print(Panel(
                "[yellow]This provider isn't implemented yet.\n"
                "Only [bold]Gemini[/] and [bold]Local (Ollama)[/] are available right now.[/]",
                border_style="yellow"
            ))
            console.input("\n[dim]Press Enter to continue...[/]")
            continue

        # Persist provider immediately
        edit_config(provider=provider_choice)

        # Step 2: fetch models and show searchable picker
        _pick_model_for_provider(provider_choice)

def _pick_model_for_provider(provider: str) -> None:
    """
    Step 2 of model selection: fetch the model list for the given provider
    and show a searchable autocomplete prompt.

    Typing narrows the list in real time; leaving the field empty lists all
    models. The currently selected model is shown at the top of the list.
    """
    clear_console()
    console.print(BANNER)

    # --- Fetch model list ---------------------------------------------------
    models: list[str] = []
    label = provider.title()

    if provider == "gemini":
        try:
            from src.tofetchmodal import generate_models_list
            models = list(generate_models_list)
            label = "Gemini"
        except Exception as e:
            console.print(f"[red]Could not load Gemini models: {e}[/]")
            console.input("\n[dim]Press Enter to continue...[/]")
            return

    elif provider == "local":
        console.print("[dim]Querying Ollama for available models...[/]")
        try:
            from src.providers.local import LocalProvider
            cfg = get_config()
            p = LocalProvider(cfg, "")
            models = p.get_available_models()
            label = "Local (Ollama)"
        except ImportError:
            console.print(Panel(
                "[red]The 'ollama' package is not installed.\n\n"
                "Install it with:[/]\n[bold]pip install ollama[/]",
                title="[bold]Ollama Not Installed[/]",
                border_style="red"
            ))
            console.input("\n[dim]Press Enter to continue...[/]")
            return
        except Exception as e:
            console.print(Panel(
                f"[yellow]Could not reach Ollama server.\n\n"
                f"Make sure Ollama is running:[/]\n[bold]ollama serve[/]\n\n"
                f"[dim]Error: {e}[/]",
                title="[bold]Ollama Unreachable[/]",
                border_style="yellow"
            ))
            console.input("\n[dim]Press Enter to continue...[/]")
            return

    if not models:
        console.print(f"[yellow]No models found for {label}.[/]")
        console.input("\n[dim]Press Enter to continue...[/]")
        return

    # --- Build display -------------------------------------------------------
    current_model = get_config().get("default_model", "")

    # Put the currently active model first so it shows up immediately
    ordered = []
    if current_model in models:
        ordered.append(current_model)
    for m in models:
        if m != current_model:
            ordered.append(m)

    console.print(Panel(
        f"[cyan]Provider:[/] [bold]{label}[/]   "
        f"[cyan]Active model:[/] [bold]{current_model or 'none'}[/]\n\n"
        "[dim]Start typing to filter \u2014 press Tab/Enter to select[/]",
        title="Step 2 \u2014 Choose a model",
        border_style="blue"
    ))
    console.print("")

    selected = questionary.autocomplete(
        "Search or select a model:",
        choices=ordered,
        default=current_model if current_model in ordered else "",
        match_middle=True,
        qmark="\u25b6",
        style=custom_style,
    ).ask()

    if selected and selected.strip():
        chosen = selected.strip()
        if chosen not in models:
            # User typed something not in the list — warn but allow
            console.print(f"[yellow]'{chosen}' is not in the fetched list. Saving anyway.[/]")
        edit_config(model=chosen)
        console.print(f"\n[green]\u2713 Provider set to [bold]{provider}[/], model set to [bold]{chosen}[/][/]")
        time.sleep(1.2)

def _api_config_menu():
    """API configuration for different providers - writes to .env file."""
    while True:
        clear_console()
        console.print(BANNER)

        # Reload .env to get current values
        load_dotenv(override=True)

        # Check which keys are set from .env
        has_gemini = bool(os.getenv("GEMINI_API_KEY"))
        has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        status_text = ""
        status_text += f"[cyan]Gemini:[/] {'[green]✓ Set[/]' if has_gemini else '[red]✗ Not set[/]'}\n"
        status_text += f"[cyan]Ollama (Local):[/] [green]No key required[/] [dim](host: {ollama_host})[/]\n"
        status_text += f"[cyan]OpenRouter:[/] {'[green]✓ Set[/]' if has_openrouter else '[yellow]Not set[/]'}\n"
        status_text += f"[cyan]OpenAI:[/] {'[green]✓ Set[/]' if has_openai else '[yellow]Not set[/]'}\n"
        status_text += f"[cyan]Anthropic:[/] {'[green]✓ Set[/]' if has_anthropic else '[yellow]Not set[/]'}\n"

        console.print(Panel(
            status_text,
            title="API Keys (stored in .env)",
            border_style="blue"
        ))
        console.print("")

        choice = questionary.select(
            "Configure API key:",
            choices=[
                Choice(
                    title="Set Gemini API key",
                    description="Google Gemini - writes GEMINI_API_KEY to .env",
                    value="Gemini"
                ),
                Choice(
                    title="Set Ollama host",
                    description="Local Ollama server URL (default: http://localhost:11434)",
                    value="Ollama"
                ),
                Choice(
                    title="Set OpenRouter API key",
                    description="OpenRouter - writes OPENROUTER_API_KEY to .env",
                    value="OpenRouter"
                ),
                Choice(
                    title="Set OpenAI API key",
                    description="OpenAI ChatGPT - writes OPENAI_API_KEY to .env",
                    value="OpenAI"
                ),
                Choice(
                    title="Set Anthropic API key",
                    description="Anthropic Claude - writes ANTHROPIC_API_KEY to .env",
                    value="Anthropic"
                ),
                Choice(
                    title="Back",
                    description="Return to settings",
                    value="Back"
                )
            ],
            qmark="▶",
            style=custom_style
        ).ask()

        if choice == "Back" or choice is None:
            break

        if choice == "Ollama":
            # Special handling: Ollama doesn't need an API key, just a host URL
            current_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            console.print(f"\n[cyan]Current Ollama host:[/] [bold]{current_host}[/]")
            console.print("[dim]Leave blank to keep the current value.[/]\n")
            new_host = questionary.text(
                "Ollama host URL:",
                default=current_host
            ).ask()
            if new_host and new_host.strip() and new_host.strip() != current_host:
                _set_env_var("OLLAMA_HOST", new_host.strip())
                load_dotenv(override=True)
                console.print(f"[green]✓ Ollama host saved to .env[/]")
            else:
                console.print("[dim]No change.[/]")
            time.sleep(1)
            continue

        # Prompt for API key
        env_var_name = f"{choice.upper()}_API_KEY"
        console.print(f"\n[cyan]Enter your {choice} API key:[/]")
        api_key = questionary.password("API Key").ask()

        if api_key and api_key.strip():
            api_key = api_key.strip()
            # Write to .env file
            _set_env_var(env_var_name, api_key)
            # Reload .env to update os.getenv
            load_dotenv(override=True)
            console.print(f"[green]✓ {choice} API key saved to .env[/]")
            time.sleep(1)
        else:
            console.print("[yellow]No key entered.[/]")
            time.sleep(1)

def _set_env_var(key, value):
    """Set an environment variable in the .env file."""
    env_path = ".env"
    lines = []
    key_found = False

    # Read existing .env
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            lines = f.readlines()

    # Update or add the key
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}\n")
            key_found = True
        elif line.strip() and not line.strip().startswith("#"):
            new_lines.append(line)
        elif line.strip().startswith("#"):
            # Keep comment lines as-is
            new_lines.append(line)

    if not key_found:
        # Add a newline before new key if file had content
        if new_lines and any(l.strip() for l in new_lines):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")

    # Write back
    with open(env_path, "w") as f:
        f.writelines(new_lines)

def show_plugins():
    """Display loaded plugins."""
    while True:
        clear_console()
        console.print(BANNER)

        discover_plugins()
        if not PLUGINS:
            console.print(Panel(
                "[yellow]No plugins installed.\n\n"
                "Place Python modules (.py files) in the [bold]plugins/[/] directory.\n"
                "Plugins must define a [cyan]plugin_menu()[/] function that returns\n"
                "[bold](label, handler)[/] tuple.[/]",
                title="[bold red]No Plugins Found[/]",
                border_style="red"
            ))
        else:
            plugin_list = "\n".join([f"  [cyan]✓ {label}[/]" for label, _ in PLUGINS])
            console.print(Panel(
                plugin_list,
                title=f"[bold green]{len(PLUGINS)} Plugin(s) Loaded[/]",
                border_style="green"
            ))

        choice = questionary.select(
            "",
            choices=["Back"],
            qmark="▶",
            style=custom_style
        ).ask()
        break

def choose_chat():
    """Enhanced chat selector with metadata, search, and sorting by activity."""
    clear_console()
    console.print(BANNER)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query chat metadata with last message snippet, sorted by last activity
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

    # Build choices for questionary
    choices = []

    for row in rows:
        chat_id, name, msg_count, last_active, snippet = row

        # Format last_active timestamp
        if last_active:
            try:
                # Handle both string and datetime
                if isinstance(last_active, str):
                    dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                else:
                    dt = last_active
                active_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                active_str = str(last_active)[:16]
        else:
            active_str = "Never"

        # Truncate snippet for display
        snippet_display = ""
        if snippet:
            snippet_clean = snippet.replace("\n", " ").strip()
            if len(snippet_clean) > 50:
                snippet_display = snippet_clean[:47] + "..."
            else:
                snippet_display = snippet_clean

        # Build description
        desc_parts = [f"{msg_count} msgs", f"Last: {active_str}"]
        if snippet_display:
            desc_parts.append(f'"{snippet_display}"')
        description = " • ".join(desc_parts)

        choices.append(Choice(title=name, description=description, value=name))

    # Add navigation choices
    choices.insert(0, Choice(title="Create new chat", description="Start a fresh conversation", value=None))
    choices.append(Choice(title="Back", description="Return to main menu", value="__back__"))

    # Prompt
    result = questionary.select(
        "Select a chat:",
        choices=choices,
        qmark=" ❯ "
    ).ask()

    if result == "__back__":
        return None
    elif result is None:
        # "Create new chat" selected - ask for name
        new_name = questionary.text("Enter new chat name:").ask()
        if new_name and new_name.strip():
            return new_name.strip()
        return None
    else:
        # Existing chat name
        return result

def get_chat_id_by_name(chat_name, cursor):
    cursor.execute("SELECT id FROM chats WHERE name=?", (chat_name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        # Chat doesn't exist yet, create it
        cursor.execute("INSERT INTO chats (name) VALUES (?)", (chat_name,))
        cursor.connection.commit()
        return cursor.lastrowid


def rename_chat():
    """Rename an existing chat."""
    clear_console()
    console.print(BANNER)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all chats
    cursor.execute("SELECT name FROM chats ORDER BY created_at")
    chats = [row[0] for row in cursor.fetchall()]

    if not chats:
        console.print(Panel(
            "[yellow]No chats available to rename.\n"
            "Create a chat first from the main menu.[/]",
            title="[bold red]No Chats Found[/]",
            border_style="red"
        ))
        conn.close()
        return None

    # Choose chat to rename
    selected = questionary.select(
        "Select a chat to rename:",
        choices=chats + ["Back"],
        qmark="▶",
        style=custom_style
    ).ask()

    if selected == "Back":
        conn.close()
        return None

    old_name = selected
    console.print(f"\n[cyan]Renaming chat:[/cyan] [bold]{old_name}[/]\n")

    # Prompt for new name
    new_name = questionary.text(
        "Enter new name:",
        default=old_name,
        qmark="✎"
    ).ask()

    if not new_name or new_name.strip() == "":
        console.print("[yellow]Rename cancelled.[/]")
        conn.close()
        return None

    new_name = new_name.strip()

    # Check if new name already exists (and not same as old)
    cursor.execute("SELECT id FROM chats WHERE name=?", (new_name,))
    row = cursor.fetchone()
    if row and new_name != old_name:
        console.print(f"[red]A chat named '[bold]{new_name}[/]' already exists![/]")
        conn.close()
        return None

    # Update database
    cursor.execute("UPDATE chats SET name=? WHERE name=?", (new_name, old_name))
    conn.commit()
    conn.close()

    # Show success message
    console.print(f"\n[bold green]✓[/] Chat renamed to [cyan]{new_name}[/]")
    time.sleep(3)  # Pause so user sees the confirmation
    return new_name

def delete_chat():
    clear_console()
    console.print(BANNER)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all chats
    cursor.execute("SELECT name FROM chats ORDER BY created_at")
    chats = [row[0] for row in cursor.fetchall()]

    if not chats:
        console.print(Panel(
            "[yellow]No chats available to delete.\n"
            "Create a chat first from the main menu.[/]",
            title="[bold red]No Chats Found[/]",
            border_style="red"
        ))
        conn.close()
        return None

    choices = chats + ["Back"]
    selected = questionary.select(
        "Select a chat to delete:",
        choices=choices,
        qmark="▶",
        style=custom_style
    ).ask()

    if selected == "Back":
        conn.close()
        return None

    chat_name = selected
    console.print(f"\n[yellow]⚠  WARNING: About to delete chat[/yellow] [cyan]'{chat_name}'[/cyan]")
    console.print("[yellow]This action cannot be undone![/]\n")

    confirm = questionary.confirm(
        "Are you absolutely sure?",
        default=False,
        qmark="❓"
    ).ask()

    if confirm:
        # Get chat ID
        cursor.execute("SELECT id FROM chats WHERE name=?", (chat_name,))
        row = cursor.fetchone()
        if row:
            chat_id = row[0]
            # Delete messages first (FK constraint)
            cursor.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
            # Delete chat
            cursor.execute("DELETE FROM chats WHERE id=?", (chat_id,))
            conn.commit()
            console.print(f"\n[bold red]✗[/] Chat '[strike]{chat_name}[/]' deleted.")
            time.sleep(3)  # Pause so user sees the confirmation
        else:
            console.print(f"[red]Chat '{chat_name}' not found in DB![/]")
    else:
        console.print("[yellow]Deletion cancelled.[/]")
        time.sleep(3)  # Pause so user sees the message

    conn.close()

def run_chat(chat_name, chat_id=None, ui_mode=None):
    """Run a chat session in the current terminal. Returns when user exits."""
    from src.brain import Brain
    from src.chat_ui import ChatRenderer
    from rich.theme import Theme
    from prompt_toolkit.styles import Style

    cfg = get_config()
    is_tui = False
    # Determine UI mode if not provided
    if ui_mode is None:
        ui_mode = cfg.get("ui", {}).get("mode", "cli")

    # If chat_id not provided, get or create it
    if chat_id is None:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        chat_id = get_chat_id_by_name(chat_name, cursor)
        conn.close()

    # Create brain (logic layer) - loads history but NOT model yet
    brain = Brain(cfg, chat_name=chat_name, chat_id=chat_id)

    # Choose renderer based on UI mode
    if ui_mode == "tui":
        try:
            from src.tui_renderer import TUIChatRenderer, HelpScreen
            renderer = TUIChatRenderer()
            renderer.start()
            is_tui = True
        except ImportError:
            console.print("[red]Textual not installed. Falling back to CLI.[/]")
            console.input("\n[dim]Press Enter to continue...[/]")
            renderer = ChatRenderer(code_theme=Theme({
                "markdown.code": "on #1e1e1e #f8f8f2",
                "markdown.code_block": "on #1e1e1e #f8f8f2",
            }))
    else:
        renderer = ChatRenderer(code_theme=Theme({
            "markdown.code": "on #1e1e1e #f8f8f2",
            "markdown.code_block": "on #1e1e1e #f8f8f2",
        }))

    # Render chat history immediately (before model loading)
    for message in brain.get_history():
        role = message["role"]
        content = "\n".join(message["parts"]).strip()
        timestamp = message.get("timestamp")
        renderer.render_message(role, content, timestamp, brain.show_timestamps)

        # Separator after model messages (except last)
        if role == "model" and message != brain.get_history()[-1]:
            renderer.render_separator()

    renderer.render_blank_line()
    renderer.render_separator()

    # Start model loading in background (will wait for it before showing prompt)
    import threading
    def load_model_and_check():
        try:
            brain.initialize_provider()
            # Start background refresh thread (every 1 hour)
            brain.start_background_model_refresh(interval_hours=1)
        except Exception as e:
            brain.load_error = str(e)

    # Start loading in daemon thread
    loader_thread = threading.Thread(target=load_model_and_check, daemon=True)
    loader_thread.start()

    # Show a spinner while waiting for model to load
    if not is_tui:
        spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        frame_idx = 0
        renderer.console.print("")  # ensure on fresh line
        while not brain.is_model_loaded():
            if brain.load_error:
                renderer.console.print(f"[bold red]Failed to load model: {brain.load_error}[/bold red]")
                renderer.console.input("\n[dim]Press Enter to return to main menu...[/]")
                brain.close()  # cleanup db connection
                return
            frame = spinner_frames[frame_idx]
            renderer.console.print(f"[red]{frame} Loading model...[/red]", end="\r")
            frame_idx = (frame_idx + 1) % len(spinner_frames)
            time.sleep(0.1)
        # Clear spinner line and add blank line before input
        renderer.console.print(" " * 40)  # clear the line
        renderer.console.print("")  # blank line before input
    else:
        renderer.show_status("Loading model...")
        while not brain.is_model_loaded():
            if brain.load_error:
                renderer.show_error(f"Failed to load model: {brain.load_error}")
                renderer.show_status("Press Enter to return to main menu...")
                if is_tui:
                    renderer.stop()
                brain.close()
                return
            time.sleep(0.1)
        renderer.show_status("")  # clear status

    # Start main chat loop with input prompt and status bar
    while True:
        chat_info = brain.get_metadata()
        # For TUI, update renderer's chat_info for info bar
        if is_tui:
            renderer.chat_info = chat_info
        # Get user input
        user_input = renderer.get_input(chat_info).strip()

        # Handle slash commands
        if user_input.startswith('/'):
            result = brain.handle_command(user_input[1:])
            action = result.get("action")

            if is_tui:
                # TUI-specific command handling
                if action == "exit":
                    renderer.render_blank_line()
                    renderer.show_status("Goodbye, human. See you later :)")
                    break
                elif action == "clear":
                    # Clear the messages log
                    renderer.app.call_from_thread(renderer.app.query_one("#messages").clear)
                elif action == "help":
                    # Show help screen
                    renderer.app.call_from_thread(renderer.app.push_screen, HelpScreen())
                elif action == "message":
                    # Show command message in status bar
                    renderer.show_status(result.get("message", ""))
                elif action == "status":
                    data = result["data"]
                    status_str = f"Chat: {data['chat']} | Model: {data['model']} | Exchanges: {data['exchanges']} | Tokens: ~{data['tokens']} | Timestamps: {data['timestamps']}"
                    renderer.show_status(status_str)
                elif action == "select_model" or action == "refresh_model":
                    renderer.show_status("Model switching not implemented in TUI yet")
                else:
                    renderer.show_status(f"Unknown command: /{user_input[1:]}")
                renderer.render_blank_line()
                continue
            else:
                # CLI command handling (original)
                if action == "exit":
                    renderer.console.print("")
                    renderer.console.print("[dim]Goodbye, human. See you later :)[/dim]")
                    break
                elif action == "clear":
                    renderer.console.clear()
                elif action == "help":
                    _show_help(renderer)
                elif action == "message":
                    renderer.console.print(result.get("message", ""))
                    renderer.console.input("\n[dim]Press Enter to continue...[/]")
                elif action == "status":
                    _show_status(renderer, result["data"])
                elif action == "select_model":
                    _handle_model_switch(renderer, brain, result["models"])
                elif action == "refresh_model":
                    _handle_refresh_model(renderer, brain)
                else:
                    # Continue loop without extra output
                    pass

                renderer.console.print("")
                continue

        # Normal message exchange
        renderer.render_blank_line()

        response_text, model_ts = brain.send_message(user_input)

        # Render response
        renderer.render_message("model", response_text, model_ts, brain.show_timestamps)

        # Separator
        renderer.render_separator()

    if is_tui:
        renderer.stop()
    brain.close()

def _show_help(renderer):
    """Display help text."""
    renderer.console.print("\n[bold]Available commands:[/]")
    renderer.console.print("  /help - Show this help")
    renderer.console.print("  /exit - Return to main menu")
    renderer.console.print("  /save - Save chat to JSON file")
    renderer.console.print("  /copy - Copy last Nomi response to clipboard")
    renderer.console.print("  /clear - Clear the screen")
    renderer.console.print("  /export [filename] - Export chat to Markdown")
    renderer.console.print("  /status - Show detailed status")
    renderer.console.print("  /model - Switch AI model")
    renderer.console.print("  /refresh_model - Check for better models and auto-upgrade")
    renderer.console.print("  /timestamp - Toggle timestamps")
    renderer.console.print("  /animation - Toggle animations")
    renderer.console.input("\nPress Enter to continue...")

def _show_status(renderer, data):
    """Display chat status."""
    renderer.console.print(f"\n[bold]Status:[/]")
    renderer.console.print(f"  Chat: {data['chat']}")
    renderer.console.print(f"  Model: {data['model']}")
    renderer.console.print(f"  Exchanges: {data['exchanges']}")
    renderer.console.print(f"  Approx tokens: ~{data['tokens']}")
    renderer.console.print(f"  Timestamps: {data['timestamps']}")
    renderer.console.print("")

def _handle_model_switch(renderer, brain, models):
    """Handle model selection from available list."""
    if not models:
        renderer.console.print("[yellow]No models available.[/]")
        renderer.console.input("\n[dim]Press Enter to continue...[/]")
        return

    current_model = brain.model_name
    # Build choices with current model marked
    choices = []
    for model in models:
        prefix = "[bold green]✓[/] " if model == current_model else "  "
        choices.append(f"{prefix}{model}")

    choices.append("Cancel")

    selected = questionary.select(
        "Select model to switch to:",
        choices=choices,
        qmark="▶",
        style=custom_style
    ).ask()

    if selected == "Cancel" or selected is None:
        renderer.console.print("[yellow]Model switch cancelled.[/]")
        return

    # Extract model name (remove prefix)
    model_name = selected.replace("[bold green]✓[/] ", "").strip()

    if model_name == current_model:
        renderer.console.print(f"[cyan]Already using {model_name}[/]")
        return

    # Attempt switch with spinner
    with renderer.console.status(f"[bold cyan]Switching to {model_name}...[/bold cyan]", spinner="dots"):
        success, error = brain.switch_model(model_name)

    if success:
        renderer.console.print(f"[bold green]✓[/] Switched to model: [cyan]{model_name}[/]")
        # Brief pause to show success
        import time
        time.sleep(1)
    else:
        renderer.console.print(f"[bold red]✗[/] Failed to switch: {error}")

def _handle_refresh_model(renderer, brain):
    """Check for better models and switch if available."""
    renderer.console.print("\n[bold cyan]Checking for better models...[/bold cyan]")

    # Use spinner while checking
    with renderer.console.status("[bold cyan]Testing available models...[/bold cyan]", spinner="dots"):
        better_model = brain.find_better_model()

    if better_model:
        # Auto-switch to better model
        with renderer.console.status(f"[bold cyan]Switching to {better_model}...[/bold cyan]", spinner="dots"):
            success, error = brain.switch_model(better_model)

        if success:
            renderer.console.print(f"[bold green]✓[/] Upgraded to better model: [cyan]{better_model}[/]")
            renderer.console.print(f"[dim]Model change will take effect on next message.[/]")
        else:
            renderer.console.print(f"[bold red]✗[/] Failed to switch: {error}")
    else:
        renderer.console.print("[green]✓[/] Current model is optimal. No better models found.")

def main_menu():
    while True:
        system = platform.system().lower()
        clear_console()
        console.print(BANNER)

        # Use styled choices with descriptions
        choice = questionary.select(
            "What would you like to do?",
            choices=[
                Choice(
                    title="Open/Create Chat",
                    description="Start a new conversation or continue an existing one",
                    value="Open/Create Chat"
                ),
                Choice(
                    title="Rename Chat",
                    description="Change the name of an existing chat",
                    value="Rename Chat"
                ),
                Choice(
                    title="Delete Chat",
                    description="Permanently remove a chat and its history",
                    value="Delete Chat"
                ),
                Choice(
                    title="Settings",
                    description="Configure persona, appearance, models, and plugins",
                    value="Settings"
                ),
                Choice(
                    title="Plugins",
                    description="View and manage installed plugins",
                    value="Plugins"
                ),
                Choice(
                    title="Exit",
                    description="Quit Nomi",
                    value="Exit"
                ),
            ],
            qmark="▶",
            style=custom_style
        ).ask()

        if choice == "Open/Create Chat":
            chat_name = choose_chat()
            if chat_name is None:
                continue
            # Ask for UI mode
            cfg = get_config()
            current_mode = cfg.get("ui", {}).get("mode", "cli")
            console.print("\n[bold]Select Interface:[/]")
            ui_mode = questionary.select(
                "Which interface to use?",
                choices=[
                    Choice(title="CLI", description="Classic command-line interface", value="cli"),
                    Choice(title="TUI", description="Modern Textual terminal UI", value="tui")
                ],
                default=current_mode,
                qmark="▶",
                style=custom_style
            ).ask()
            if ui_mode is None:
                continue  # User cancelled
            clear_console()
            run_chat(chat_name, ui_mode=ui_mode)
        if choice == "Rename Chat":
            rename_chat()
        if choice == "Delete Chat":
            delete_chat()
        elif choice == "Settings":
            settings_menu()
        elif choice == "Exit":
            clear_console()
            break
