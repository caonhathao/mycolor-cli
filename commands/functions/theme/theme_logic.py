import json
import os
import sys

from prompt_toolkit.styles import Style as PTStyle
from core.theme_engine import (
    THEMES,
    DEFAULT_THEME,
    set_theme as core_set_theme,
    apply_theme as core_apply_theme,
    get_current_theme as core_get_current_theme,
    get_current_theme_colors as core_get_current_theme_colors,
    get_app_style as core_get_app_style,
    get_current_theme_name as core_get_current_theme_name,
)
from core.theme_engine import get_pt_color_hex as core_get_pt_color_hex

THEMES = THEMES
DEFAULT_THEME = DEFAULT_THEME

DEFAULT_CONFIG = {
    "window_settings": {
        "cols": 120,
        "lines": 30,
        "auto_resize": True,
        "force_full_width": True
    },
    "layout_visibility": {
        "performance": {
            "show_sidebar": False,
            "rendered_components": ["graphs"]
        }
    },
    "process_update_interval": 3.0,
    "net_max_speed_mbps": 100,
    "last_export_path": "",
    "customs": {
        "theme": "matrix",
    }
}

_config_path = None
_fallback_path_used = False


def _get_settings_path():
    """Returns the path to settings.json, handling frozen (.exe) mode."""
    global _config_path
    if _config_path is not None:
        return _config_path

    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    _config_path = os.path.join(base_dir, "config", "settings.json")
    return _config_path


def _get_config_dir():
    """Backward-compatible alias for _get_settings_path()."""
    return _get_settings_path()


def get_config_dir():
    """Returns the directory where config should be stored."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "config")


def ensure_config_exists():
    """Creates default settings.json if it doesn't exist. Returns path to config."""
    global _fallback_path_used

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_dir = os.path.join(base_dir, "config")
    config_path = os.path.join(config_dir, "settings.json")

    try:
        os.makedirs(config_dir, exist_ok=True)
        if os.path.exists(config_path):
            return config_path
    except OSError:
        pass

    default_config = DEFAULT_CONFIG.copy()
    test_write_path = os.path.join(config_dir, ".write_test")

    try:
        with open(test_write_path, "w") as f:
            f.write("test")
        os.remove(test_write_path)
        write_dir = config_dir
    except (IOError, OSError):
        write_dir = os.path.join(os.environ.get("APPDATA", ""), "MyWorldCLI")
        _fallback_path_used = True

    try:
        os.makedirs(write_dir, exist_ok=True)
    except OSError:
        write_dir = os.environ.get("TEMP", "")

    config_path = os.path.join(write_dir, "settings.json")

    try:
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        _config_path = config_path
        print(f"[MYCOLOR] Created default config at: {config_path}")
    except (IOError, OSError):
        pass

    return config_path


def set_theme(theme_name, save=True):
    """Sets the current theme. Delegates to core theme_engine."""
    return core_set_theme(theme_name, save=save)


def apply_theme(theme_name):
    """Apply theme globally without saving - syncs UI without file write."""
    return core_apply_theme(theme_name)


def load_config():
    """Loads theme from settings.json - handled by core theme_engine."""
    pass


def save_config():
    """Saves current theme to settings.json - handled by core theme_engine."""
    pass


def get_current_theme():
    """Returns current theme dict. Delegates to core theme_engine."""
    return core_get_current_theme()


def get_current_theme_colors():
    """Returns a dictionary of all theme colors for UI components."""
    return core_get_current_theme_colors()


def get_pt_color_hex(rich_style) -> str:
    """Converts a rich.Style's color or string to prompt_toolkit-compatible 6-char hex."""
    return core_get_pt_color_hex(rich_style)


def get_app_style():
    """Returns the prompt_toolkit Style object based on the current theme."""
    return core_get_app_style()


def get_current_theme_name():
    """Returns the current theme name."""
    return core_get_current_theme_name()
