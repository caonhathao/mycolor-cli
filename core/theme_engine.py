import json
import os
import sys

from prompt_toolkit.styles import Style as PTStyle

THEMES = {
    "classic": {
        "primary": "#888888",
        "secondary": "#ffffff",
        "background": "#1c1c1c",
        "suggestion_bg": "#333333",
        "logo_gradient": ["#ffffff", "#888888", "#444444"],
        "logo_shadow": "#696969",
        "table_border": "#444444",
        "table_header": "#888888",
        "table_text": "#ffffff",
        "active_tab": "#FFFF00",
        "tab_accent": "#FFFF00",
        "inactive_tab": "#888888",
        "monitor_graph": "#00FF00",
        "monitor_text": "#ffffff",
        "success": "#00FF41",
        "error": "#FF0000",
        "warning": "#FFFF00",
        "header_bg": "#1c1c1c",
        "header_text": "#888888",
        "cursor": "#494949",
    },
    "matrix": {
        "primary": "#00FF41",
        "secondary": "#003B00",
        "background": "#000500",
        "suggestion_bg": "#002200",
        "logo_gradient": ["#00FF41", "#008F11", "#003B00"],
        "logo_shadow": "#001100",
        "table_border": "#003B00",
        "table_header": "#00FF41",
        "table_text": "#00FF41",
        "active_tab": "#00FF41",
        "tab_accent": "#00FF41",
        "inactive_tab": "#004400",
        "monitor_graph": "#00FF41",
        "monitor_text": "#00FF41",
        "success": "#00FF41",
        "error": "#FF0000",
        "warning": "#FFFF00",
        "header_bg": "#000500",
        "header_text": "#00FF41",
        "cursor": "#00FF41",
    },
    "cyber": {
        "primary": "#FF007F",
        "secondary": "#00FFFF",
        "background": "#0f0913",
        "suggestion_bg": "#2d103b",
        "logo_gradient": ["#FF007F", "#bd5aff", "#00FFFF"],
        "logo_shadow": "#501078",
        "table_border": "#501078",
        "table_header": "#FF007F",
        "table_text": "#00FFFF",
        "active_tab": "#FF007F",
        "tab_accent": "#FF007F",
        "inactive_tab": "#501078",
        "monitor_graph": "#00FFFF",
        "monitor_text": "#FF007F",
        "success": "#00FF00",
        "error": "#FF0000",
        "warning": "#FFFF00",
        "header_bg": "#0f0913",
        "header_text": "#FF007F",
        "cursor": "#FF007F",
    },
    "darcula": {
        "primary": "#A9B7C6",
        "secondary": "#CC7832",
        "background": "#2B2B2B",
        "suggestion_bg": "#3B3F41",
        "logo_gradient": ["#CC7832", "#9876AA", "#6A8759"],
        "logo_shadow": "#1E1E1E",
        "table_border": "#3B3F41",
        "table_header": "#A9B7C6",
        "table_text": "#A9B7C6",
        "active_tab": "#CC7832",
        "tab_accent": "#CC7832",
        "inactive_tab": "#3B3F41",
        "monitor_graph": "#6A8759",
        "monitor_text": "#A9B7C6",
        "success": "#6A8759",
        "error": "#CC7832",
        "warning": "#FFC66D",
        "header_bg": "#2B2B2B",
        "header_text": "#A9B7C6",
        "cursor": "#A9B7C6",
    },
}

DEFAULT_THEME = "matrix"

current_theme_name = DEFAULT_THEME
current_theme = THEMES[current_theme_name]


def _get_settings_path():
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "config", "settings.json")


def set_theme(theme_name: str, save: bool = True) -> bool:
    global current_theme_name, current_theme
    if theme_name in THEMES:
        current_theme_name = theme_name
        current_theme = THEMES[theme_name]
        if save:
            _save_theme_to_config(theme_name)
        return True
    return False


def apply_theme(theme_name: str) -> bool:
    global current_theme_name, current_theme
    if theme_name in THEMES:
        current_theme_name = theme_name
        current_theme = THEMES[theme_name]
        return True
    return False


def load_theme_from_config():
    try:
        config_path = _get_settings_path()
        with open(config_path, "r") as f:
            config = json.load(f)
            customs = config.get("customs", {})
            theme_name = customs.get("theme")
            if theme_name:
                apply_theme(theme_name)
    except (IOError, json.JSONDecodeError):
        pass


def _save_theme_to_config(theme_name: str):
    try:
        config_path = _get_settings_path()
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}

        if "customs" not in config:
            config["customs"] = {}
        config["customs"]["theme"] = theme_name

        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
    except IOError:
        pass


def get_current_theme():
    return current_theme


def get_current_theme_colors():
    primary_hex = get_pt_color_hex(current_theme.get("primary"))
    secondary_hex = get_pt_color_hex(current_theme.get("secondary"))
    return {
        "primary": primary_hex,
        "secondary": secondary_hex,
        "background": current_theme.get("background", "#1c1c1c"),
        "suggestion_bg": current_theme.get("suggestion_bg", "#21262d"),
        "table_border": current_theme.get("table_border", "#444444"),
        "table_header": get_pt_color_hex(current_theme.get("table_header", "white")),
        "table_text": get_pt_color_hex(current_theme.get("table_text", "white")),
        "active_tab": current_theme.get("active_tab", "#FFFF00"),
        "tab_accent": current_theme.get("tab_accent", "#FFFF00"),
        "inactive_tab": current_theme.get("inactive_tab", "#888888"),
        "monitor_graph": current_theme.get("monitor_graph", "#00FF00"),
        "monitor_text": get_pt_color_hex(current_theme.get("monitor_text", "white")),
        "success": current_theme.get("success", "green"),
        "error": current_theme.get("error", "red"),
        "warning": current_theme.get("warning", "yellow"),
        "header_bg": current_theme.get("header_bg", "#1c1c1c"),
        "header_text": get_pt_color_hex(current_theme.get("header_text", "white")),
        "cursor": current_theme.get("cursor", "white"),
    }


def get_pt_color_hex(rich_style) -> str:
    if rich_style is None:
        return "#c0c0c0"
    if isinstance(rich_style, str):
        if rich_style.startswith("#"):
            return rich_style
        return rich_style
    if hasattr(rich_style, "color") and rich_style.color:
        try:
            color_obj = rich_style.color
            if hasattr(color_obj, "get_truecolor"):
                triplet = color_obj.get_truecolor()
                return f"#{triplet.red:02x}{triplet.green:02x}{triplet.blue:02x}"
            elif hasattr(color_obj, "name"):
                return color_obj.name
        except Exception:
            pass
    return "#c0c0c0"


def get_app_style():
    primary_hex = get_pt_color_hex(current_theme["primary"])
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
            "footer-divider": f"fg:#444444",
            "completion-menu": f"bg:{suggestion_bg}",
            "completion-menu.completion": f"bg:{suggestion_bg} fg:{primary_hex}",
            "completion-menu.completion.current": f"bg:{primary_hex} fg:#000000",
            "scrollbar": f"bg:{current_theme['background']}",
            "popup-menu": f"bg:{suggestion_bg} fg:{primary_hex}",
            "popup-item": f"fg:#BBBBBB",
            "popup-selected": f"bg:{primary_hex} fg:#000000 bold",
        }
    )