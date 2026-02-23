import json
import os
from rich.style import Style
from prompt_toolkit.styles import Style as PTStyle

# --- Themes ---
THEMES = {
    "classic": {
        "primary": Style(color="grey93"),
        "secondary": Style(color="white"),
        "background": "#0d1117",
        "logo_gradient": ["#00ffff", "#bd5aff", "#ff00ff"],  # Cyan -> Purple -> Pink
        "logo_shadow": "grey30",
    },
    "matrix": {
        "primary": Style(color="green"),
        "secondary": Style(color="red"),
        "background": "#0d1117",
        "logo_gradient": ["#00ffff", "#bd5aff", "#ff00ff"],
        "logo_shadow": "grey30",
    },
    "cyber": {
        "primary": Style(color="purple"),
        "secondary": Style(color="#FF69B4"),
        "background": "#0d1117",
        "logo_gradient": ["#a020f0", "#ff007f"],  # Vibrant Purple -> Hot Pink
        "logo_shadow": "#501078",  # Dimmed Purple
    },
}

CONFIG_FILE = "config.json"
DEFAULT_THEME = "cyber"

current_theme_name = DEFAULT_THEME
current_theme = THEMES[current_theme_name]


def load_theme():
    """Loads the theme from config.json."""
    global current_theme_name, current_theme
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
                theme_name = config.get("theme", DEFAULT_THEME)
                if theme_name in THEMES:
                    current_theme_name = theme_name
                    current_theme = THEMES[current_theme_name]
                    return
    except Exception:
        pass
    
    # Fallback
    current_theme_name = DEFAULT_THEME
    current_theme = THEMES[current_theme_name]


def save_theme(theme_name):
    """Saves the current theme to config.json."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump({"theme": theme_name}, f)
    except Exception:
        pass


def set_theme(theme_name):
    """Sets the current theme and saves it."""
    global current_theme_name, current_theme
    if theme_name in THEMES:
        current_theme_name = theme_name
        current_theme = THEMES[current_theme_name]
        save_theme(theme_name)
        return True
    return False


def switch_theme():
    """Cycles through available themes and saves the selection."""
    global current_theme_name, current_theme
    theme_names = list(THEMES.keys())
    current_index = theme_names.index(current_theme_name)
    next_index = (current_index + 1) % len(theme_names)
    new_theme_name = theme_names[next_index]
    set_theme(new_theme_name)


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
    return PTStyle.from_dict(
        {
            "input-field": f"bg:{current_theme['background']} fg:{get_pt_color_hex(current_theme['primary'])}",
            "input-field text": f"bg:{current_theme['background']} fg:{get_pt_color_hex(current_theme['primary'])}",
            "input-border": f"fg:#444444 bg:{current_theme['background']}",
            "prompt-prefix": "fg:#00ffff bold",
            "placeholder": "fg:#666666 italic",
            "path": f"bg:{current_theme['background']} fg:#666666 italic",
            "sep": f"bg:{current_theme['background']} fg:#444444",
            "pc": f"bg:{current_theme['background']} fg:#666666 italic",
            "footer-pad": f"bg:{current_theme['background']}",
            "completion-menu.completion": "bg:#0d1117 fg:#c0c0c0",
            "completion-menu.completion.current": "bg:#282a36 fg:#ffffff",
            "scrollbar": f"bg:{current_theme['background']}",
        }
    )
