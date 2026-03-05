import json
import os

from prompt_toolkit.styles import Style as PTStyle
from rich.style import Style

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

DEFAULT_THEME = "matrix"

current_theme_name = DEFAULT_THEME
current_theme = THEMES[current_theme_name]


def set_theme(theme_name):
    """Sets the current theme."""
    global current_theme_name, current_theme
    if theme_name in THEMES:
        current_theme_name = theme_name
        current_theme = THEMES[current_theme_name]
        return True
    return False


def load_config():
    """Loads theme from config.json."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            theme_name = config.get("theme")
            if theme_name:
                set_theme(theme_name)
    except (IOError, json.JSONDecodeError):
        pass # Use default theme if config is missing or invalid


def get_current_theme():
    return current_theme


def get_current_theme_colors():
    """Returns a dictionary of hex colors for the current theme."""
    primary_hex = get_pt_color_hex(current_theme["primary"])
    secondary_hex = get_pt_color_hex(current_theme["secondary"])
    return {"primary": primary_hex, "secondary": secondary_hex}


def get_pt_color_hex(rich_style: Style) -> str:
    """Converts a rich.Style's color to prompt_toolkit-compatible 6-char hex. No alpha."""
    if rich_style and rich_style.color:
        try:
            color_obj = rich_style.color
            triplet = color_obj.get_truecolor()
            return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"
        except Exception:
            pass  # Fallback on error
    return "#c0c0c0"  # fallback


def get_app_style():
    """Returns the prompt_toolkit Style object based on the current theme."""
    primary_hex = get_pt_color_hex(current_theme['primary'])
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