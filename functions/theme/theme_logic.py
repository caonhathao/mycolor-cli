import json
import os
from rich.style import Style
from prompt_toolkit.styles import Style as PTStyle

# --- Themes ---
THEMES = {
    "classic": {
        "primary": Style(color="grey93"),
        "secondary": Style(color="white"),
        "background": "#1c1c1c",
        "suggestion_bg": "#333333",
        "logo_gradient": ["#00ffff", "#bd5aff", "#ff00ff"],  # Cyan -> Purple -> Pink
        "logo_shadow": "grey30",
    },
    "matrix": {
        "primary": Style(color="green"),
        "secondary": Style(color="red"),
        "background": "#000500",
        "suggestion_bg": "#002200",
        "logo_gradient": ["#00ffff", "#bd5aff", "#ff00ff"],
        "logo_shadow": "grey30",
    },
    "cyber": {
        "primary": Style(color="purple"),
        "secondary": Style(color="#FF69B4"),
        "background": "#0f0913",
        "suggestion_bg": "#2d103b",
        "logo_gradient": ["#a020f0", "#ff007f"],  # Vibrant Purple -> Hot Pink
        "logo_shadow": "#501078",  # Dimmed Purple
    },
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
DEFAULT_THEME = "matrix"
DEFAULT_WINDOW_SETTINGS = {
    "cols": 124,
    "lines": 30,
    "auto_resize": True,
    "force_full_width": True
}

current_theme_name = DEFAULT_THEME
current_theme = THEMES[current_theme_name]
current_window_settings = DEFAULT_WINDOW_SETTINGS.copy()


def save_config():
    """Saves the current config to config.json."""
    try:
        config = {
            "theme": current_theme_name,
            "window_settings": current_window_settings
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
    except Exception:
        pass


def load_config():
    """Loads the full config from config.json."""
    global current_theme_name, current_theme, current_window_settings
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                
                # Theme
                theme_name = config.get("theme", DEFAULT_THEME)
                if theme_name in THEMES:
                    current_theme_name = theme_name
                    current_theme = THEMES[theme_name]
                
                # Window Settings
                if "window_settings" in config:
                    current_window_settings.update(config["window_settings"])
                else:
                    save_config()
                
                # Validate log directory
                log_path = config.get("log_export_path")
                if log_path:
                    log_dir = os.path.dirname(log_path)
                    if log_dir:
                        os.makedirs(log_dir, exist_ok=True)
        else:
            save_config()
            # Create default log directory
            default_log = os.path.join(os.path.expanduser("~"), "Documents", "mycolor", "log")
            os.makedirs(default_log, exist_ok=True)
    except Exception:
        pass


def load_theme():
    """Legacy alias for load_config."""
    load_config()


def save_theme(theme_name):
    """Sets the current theme and saves it."""
    global current_theme_name, current_theme
    if theme_name in THEMES:
        current_theme_name = theme_name
        current_theme = THEMES[current_theme_name]
        save_config()
        return True
    return False

def set_theme(theme_name):
    """Sets the current theme and saves it."""
    global current_theme_name, current_theme
    if theme_name in THEMES:
        current_theme_name = theme_name
        current_theme = THEMES[current_theme_name]
        save_config()
        return True
    return False


def get_pt_color_hex(rich_style: Style) -> str:
    """Converts a rich.Style's color to prompt_toolkit-compatible 6-char hex. No alpha."""
    try:
        if rich_style and rich_style.color:
            color_obj = rich_style.color
            triplet = color_obj.get_truecolor()
            return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"
    except Exception:
        pass
    return "#c0c0c0"  # fallback


def get_app_style():
    """Returns the prompt_toolkit Style object based on the current theme."""
    primary_hex = get_pt_color_hex(current_theme['primary'])
    secondary_hex = get_pt_color_hex(current_theme['secondary'])
    suggestion_bg = current_theme.get("suggestion_bg", "#21262d")
    return PTStyle.from_dict(
        {
            "app-background": f"bg:{current_theme['background']}",
            "input-field": f"bg:{current_theme['background']} fg:{primary_hex}",
            "input-field text": f"bg:{current_theme['background']} fg:{primary_hex}",
            "input-border": f"fg:{primary_hex} bg:{current_theme['background']}",
            "frame.border": f"fg:{primary_hex} bg:{current_theme['background']}",
            "prompt-prefix": f"fg:{primary_hex} bold",
            "placeholder": "fg:#666666 italic",
            "path": f"bg:{current_theme['background']} fg:#666666 italic",
            "sep": f"bg:{current_theme['background']} fg:#444444",
            "pc": f"bg:{current_theme['background']} fg:#666666 italic",
            "footer-pad": f"bg:{current_theme['background']}",
            "completion-menu": f"bg:{suggestion_bg}",
            "completion-menu.completion": f"bg:{suggestion_bg} fg:{primary_hex}",
            "completion-menu.completion.current": f"bg:{primary_hex} fg:#000000",
            "scrollbar": f"bg:{current_theme['background']}",
        }
    )