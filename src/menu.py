#loading menu trial

import os
import warnings

# Disable questionary's built-in styling to avoid config warnings (must be before importing questionary)
os.environ['QUESTIONARY_DISABLE_STYLES'] = '1'
os.environ['QUESTIONARY_NO_STYLE'] = '1'
os.environ['QUESTIONARY_USE_ANSI_COLORS'] = '1'
os.environ['QUESTIONARY_STYLE'] = 'none'  # Force no style
os.environ['PYTHONWARNINGS'] = 'ignore'  # Suppress all warnings

# Suppress the specific warning about window_padding_height from prompt_toolkit
warnings.filterwarnings("ignore", message="Ignoring unknown config key")

import sqlite3, yaml, questionary, subprocess, platform, shutil, sys, psutil, importlib
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from questionary import Choice

# Plugin system
PLUGINS = []

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

TERMINAL_CANDIDATES_LINUX = {
    "gnome-terminal",
    "alacritty",
    "kitty",
    "wezterm",
    "xterm",
    "foot",
    "tilix",
    "konsole",
    "lxterminal",
    "xfce4-terminal",
    "urxvt",
}
TERMINAL_CANDIDATES_MAC = {
    "iTerm.app",
    "Terminal.app"
}
TERMINAL_CANDIDATES_WIN = {
    "wt",
    "powershell",
    "cmd"
}

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
                "multi_window": False,  # default to single-window TUI
            }
        else:
            if "show_timestamps" not in cfg["ui"]:
                cfg["ui"]["show_timestamps"] = True
            if "animation_enabled" not in cfg["ui"]:
                cfg["ui"]["animation_enabled"] = True
            if "character_limit" not in cfg["ui"]:
                cfg["ui"]["character_limit"] = 4000
            if "multi_window" not in cfg["ui"]:
                cfg["ui"]["multi_window"] = False
        return cfg
    except FileNotFoundError:
        # Create default config if it doesn't exist
        default_config = {
            "default_model": "gemini-1.5-flash",
            "persona": "",
            "ui": {
                "show_timestamps": True,
                "animation_enabled": True,
                "character_limit": 4000,
                "multi_window": False,
            }
        }
        with open(CONFIG_PATH, "w") as f:
            yaml.dump(default_config, f)
        return default_config

def center(text):
    return Align.center(Panel(text, expand=False))

def get_python_executable():
    system = platform.system().lower()
    if system == "windows":
        return sys.executable or "python"
    else:
        return "python3"

def clear_console():
    system = platform.system().lower()
    if system == "linux" or system == "darwin":
        os.system('clear')
    elif system == "windows":
        os.system('cls')

def detect_current_terminal():
    """
    Detects the terminal that is running this process by walking up the process tree.
    Returns the terminal executable name (like 'kitty', 'gnome-terminal', 'iTerm.app', 'wt'),
    or None if not found.
    """
    try:
        # Start from the parent of the current process
        proc = psutil.Process(os.getppid())
        visited = set()
        while proc and proc.pid not in visited:
            visited.add(proc.pid)
            name = proc.name().lower()
            # List of (substring pattern, return value) for known terminals
            patterns = [
                ("gnome-terminal", "gnome-terminal"),
                ("kitty", "kitty"),
                ("alacritty", "alacritty"),
                ("wezterm", "wezterm"),
                ("konsole", "konsole"),
                ("xfce4-terminal", "xfce4-terminal"),
                ("tilix", "tilix"),
                ("foot", "foot"),
                ("xterm", "xterm"),
                ("iTerm", "iTerm.app"),
                ("iTerm2", "iTerm.app"),
                ("Terminal", "Terminal.app"),
                ("windowsterminal", "wt"),
                ("wt.exe", "wt"),
                ("powershell", "powershell"),
                ("cmd.exe", "cmd.exe"),
                ("cmd", "cmd.exe"),
            ]
            for pattern, terminal_id in patterns:
                if pattern in name:
                    return terminal_id
            proc = proc.parent()
        return None
    except Exception:
        return None

def detect_terminal():
    cfg = get_config()
    system = platform.system().lower()
    
    # Check if we have a configured terminal AND it actually exists
    if "default_terminal" in cfg and cfg["default_terminal"]:
        configured_terminal = cfg["default_terminal"]
        
        # Verify the configured terminal actually exists
        terminal_exists = False
        if system == "linux":
            terminal_exists = shutil.which(configured_terminal) is not None
        elif system == "darwin":
            if configured_terminal.endswith(".app"):
                terminal_exists = os.path.exists(f"/Applications/{configured_terminal}")
            else:
                terminal_exists = shutil.which(configured_terminal) is not None
        elif system == "windows":
            terminal_exists = shutil.which(configured_terminal) is not None
        
        # if terminal_exists:
        #     console.print(f"[green]Using configured terminal:[/] {configured_terminal}")
        #     return configured_terminal
        # else:
        #     console.print(f"[yellow]Configured terminal '{configured_terminal}' not found, auto-detecting...[/]")
        #     # Continue to auto-detection below

    # Auto-detect available terminal
    detected_terminal = None

    if system == "linux":
        for term in TERMINAL_CANDIDATES_LINUX:
            if shutil.which(term):
                detected_terminal = term
                break
    elif system == "darwin":
        for term in TERMINAL_CANDIDATES_MAC:
            app_path = f"/Applications/{term}"
            if os.path.exists(app_path):
                detected_terminal = term
                break
    elif system == "windows":
        for term in TERMINAL_CANDIDATES_WIN:
            if shutil.which(term):
                detected_terminal = term
                break

    if detected_terminal:
        # Update config with the newly detected terminal
        # edit_config(terminal=detected_terminal)
        # console.print(f"[green]Detected and saved terminal:[/] {detected_terminal}")
        return detected_terminal
    else:
        # console.print("[red]No supported terminal found. Please install one or manually set default_terminal in config.yaml[/]")
        return None
    
def edit_config(model=None, persona=None, terminal=None, ui=None):
    # with open(CONFIG_PATH, "r") as f:
    #     cfg = yaml.safe_load(f)
    cfg = get_config()
    # if model: cfg["default_model"] = model
    if persona is not None: cfg["persona"] = persona
    # if terminal: cfg["default_terminal"] = terminal
    if ui is not None:
        cfg["ui"].update(ui)
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
    with open(CONFIG_PATH, "r") as f:
        persona = yaml.safe_load(f).get("persona", "")
    new_p = questionary.text(
        "Edit your persona (leave blank if don't want to change):",
        default=persona
    ).ask()
    return new_p if new_p.strip() != "" else None

def edit_ui_settings():
    """Interactive UI settings editor."""
    while True:
        cfg = get_config()
        ui_cfg = cfg.get("ui", {})

        # Show current settings summary
        console.print("\n[bold cyan]Current UI Settings:[/]")
        console.print(f"  Show timestamps: [yellow]{ui_cfg.get('show_timestamps', True)}[/]")
        console.print(f"  Animations enabled: [yellow]{ui_cfg.get('animation_enabled', True)}[/]")
        console.print(f"  Character limit: [yellow]{ui_cfg.get('character_limit', 4000)}[/]")
        console.print(f"  Multi-window mode: [yellow]{ui_cfg.get('multi_window', False)}[/]")
        console.print("")

        choice = questionary.select(
            "What would you like to change?",
            choices=[
                "Toggle Timestamps",
                "Toggle Animations",
                "Set Character Limit",
                "Toggle Multi-Window Mode",
                "Back"
            ],
            qmark=" ❯ "
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
                console.input("\nPress Enter to continue...")

        elif choice == "Toggle Animations":
            current = ui_cfg.get("animation_enabled", True)
            new_val = questionary.confirm(
                f"Enable animations? (currently: {current})",
                default=not current
            ).ask()
            if new_val is not None:
                edit_config(ui={"animation_enabled": new_val})
                console.print(f"[green]Animations {'enabled' if new_val else 'disabled'}[/]")
                console.input("\nPress Enter to continue...")

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
            console.input("\nPress Enter to continue...")

        elif choice == "Toggle Multi-Window Mode":
            current = ui_cfg.get("multi_window", False)
            new_val = questionary.confirm(
                f"Enable multi-window mode? (open chats in separate terminals, currently: {current})",
                default=not current
            ).ask()
            if new_val is not None:
                edit_config(ui={"multi_window": new_val})
                console.print(f"[green]Multi-window mode {'enabled' if new_val else 'disabled'}[/]")
                console.input("\nPress Enter to continue...")

def show_plugins():
    """Display loaded plugins."""
    discover_plugins()
    if not PLUGINS:
        console.print("[yellow]No plugins installed. Place Python modules in the plugins/ directory.[/]")
    else:
        console.print("[bold]Loaded Plugins:[/]")
        for label, handler in PLUGINS:
            console.print(f"  • [cyan]{label}[/]")
    console.input("\nPress Enter to continue...")

def launch_tui():
    """Launch the Textual TUI interface."""
    try:
        import subprocess
        python_exec = get_python_executable()
        # Run TUI as a separate process (will return when TUI exits)
        subprocess.run([python_exec, "-m", "src.tui.app"])
    except Exception as e:
        console.print(f"[red]Failed to launch TUI: {e}[/]")
        console.input("\nPress Enter to continue...")

def choose_chat():
    """Enhanced chat selector with metadata, search, and sorting by activity."""
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all chats
    cursor.execute("SELECT name FROM chats ORDER BY created_at")
    chats = [row[0] for row in cursor.fetchall()]

    if not chats:
        console.print("[yellow]No chats available to rename.[/]")
        conn.close()
        return None

    # Choose chat to rename
    selected = questionary.select(
        "Select a chat to rename:",
        choices=chats + ["Back"],
        qmark=" ❯ "
    ).ask()

    if selected == "Back":
        conn.close()
        return None

    old_name = selected

    # Prompt for new name
    new_name = questionary.text(
        f"Enter new name for '{old_name}':",
        default=old_name
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
        console.print(f"[red]A chat named '{new_name}' already exists![/]")
        conn.close()
        return None

    # Update database
    cursor.execute("UPDATE chats SET name=? WHERE name=?", (new_name, old_name))
    conn.commit()
    conn.close()
    return new_name

def delete_chat():
    # chats = [
    #     f[:-5] # to remove extension from the name
    #     for f in os.listdir(chat_dir)
    #     if f.endswith(".json")
    # ]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Fetch all chats
    cursor.execute("SELECT name FROM chats ORDER BY created_at")
    chats = [row[0] for row in cursor.fetchall()]

    if not chats:
        console.print("[yellow]No chats available to delete.[/]")
        conn.close()
        return None

    choices = chats + ["Back"]
    selected = questionary.select(
        "Chat to delete: ",
        choices=choices,
        qmark=" ❯ "
    ).ask()

    if selected == "Back":
        return None
    
    chat_name = selected

    confirm = questionary.confirm(
        f"Are you sure you want to delete '{chat_name}'?",
        default=False
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
            console.print(f"[bold red]Deleted chat:[/] {chat_name}")
        else:
            console.print(f"[red]Chat '{chat_name}' not found in DB![/]")
    else:
        console.print("[yellow]Deletion cancelled.[/]")

def launch_chat_window(chat_name):
    # First, try to detect the current terminal (the one running nomi)
    terminal = detect_current_terminal()

    # Validate that it's a known terminal we can launch with (not a shell like bash/zsh)
    known_terminals = (
        TERMINAL_CANDIDATES_LINUX |
        TERMINAL_CANDIDATES_MAC |
        TERMINAL_CANDIDATES_WIN
    )
    if terminal not in known_terminals:
        terminal = None

    # If that fails, fall back to config-based or auto-detection
    if not terminal:
        terminal = detect_terminal()

    if not terminal:
        console.print("[red]No terminal available. Cannot launch chat window.[/]")
        return
    
    conn = sqlite3.connect("nomi_memory.db")
    cursor = conn.cursor()
    chat_id = get_chat_id_by_name(chat_name, cursor)
    conn.close()
    
    python_exec = get_python_executable()
    cmd = [python_exec, "-m", "src.brain", chat_name]
    # cmd = [python_exec, "-m", "src.brain", chat_name, str(chat_id)]
    system = platform.system().lower()

    try:
        if system == "linux":
            if terminal in ["kitty", "alacritty"]:
                args = [terminal, "--title", f"Nomi – {chat_name}", "--"] + cmd
            elif terminal == "wezterm":
                args = [terminal, "start", "--", "bash", "-c", " ".join(cmd)]
            elif terminal == "gnome-terminal":
                args = [terminal, "--title", f"Nomi – {chat_name}", "--"] + cmd
            elif terminal in ["xfce4-terminal", "tilix"]:
                args = [terminal, "--title", f"Nomi – {chat_name}", "-e", " ".join(cmd)]
            elif terminal == "konsole":
                args = [terminal, "--new-tab", "-p", f"tabtitle=Nomi – {chat_name}", "-e"] + cmd
            elif terminal == "xterm":
                args = [terminal, "-T", f"Nomi – {chat_name}", "-e"] + cmd
            elif terminal == "foot":
                args = [terminal, "--title", f"Nomi – {chat_name}"] + cmd
            else:
                args = [terminal, "-e"] + cmd
            
            subprocess.Popen(args)

        elif system == "darwin":
            cmd_str = " ".join([f'"{arg}"' if " " in arg else arg for arg in cmd])
            if terminal == "iTerm.app":
                applescript = f'''
                tell application "iTerm"
                    create window with default profile
                    tell current session of current window
                        write text "{cmd_str}"
                        set name to "Nomi – {chat_name}"
                    end tell
                end tell
                '''
                subprocess.Popen(["osascript", "-e", applescript])
            else:  # Terminal.app
                applescript = f'''
                tell application "Terminal"
                    do script "{cmd_str}"
                    set custom title of front window to "Nomi – {chat_name}"
                end tell
                '''
                subprocess.Popen(["osascript", "-e", applescript])

        elif system == "windows":
            cmd = [python_exec, "-m", "src.brain", chat_name]
            
            subprocess.run(cmd)
            subprocess.run([python_exec, "-m", "src.menu"])
            # sys.exit(0) 

    except FileNotFoundError:
        console.print(f"[red]Terminal '{terminal}' not found![/]")
    except Exception as e:
        console.print(f"[red]Error launching terminal: {e}[/]")

def main_menu():
    while True:
        system = platform.system().lower()
        clear_console()
        console.print(("[bold cyan]\n\n  Welcome to Nomi!\n\n[/]"))

        choice = questionary.select(
            "What would you like to do?",
            choices=[
                "Open/Create Chat (Multi-Window)",
                "Open TUI (Single Window)",
                "Rename Chat",
                "Delete Chat",
                "Edit Persona",
                "Appearance Settings",
                "Plugins",
                "Exit"
            ],
            qmark=" ❯ "
        ).ask()

        if choice == "Open/Create Chat (Multi-Window)":
            chat_name = choose_chat()
            if chat_name is None:
                continue
            launch_chat_window(chat_name)
        elif choice == "Open TUI (Single Window)":
            launch_tui()
        elif choice == "Rename Chat":
            new_name = rename_chat()
            if new_name:
                console.print(f"[green]Chat renamed to: {new_name}[/]")
            console.input("\nPress Enter to continue...")
        if choice == "Delete Chat":
            dl_chat = delete_chat()
            if dl_chat is None:
                continue
            console.print(f"[bold red]Deleted:[/] {dl_chat}")
            console.print(f"\n[italic gray]Press enter to continue...[/]\n")
            input()
        # elif choice == "Change Default Model":
        #     edit_config(model=choose_model())
        elif choice == "Edit Persona":
            new_persona = edit_persona()
            if new_persona is not None:
                edit_config(persona=new_persona)
        elif choice == "Appearance Settings":
            edit_ui_settings()
        elif choice == "Plugins":
            show_plugins()
        elif choice == "Exit":
            clear_console()
            break      
