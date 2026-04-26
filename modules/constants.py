import json
import os
import sys

_SETTINGS = None
_SETTINGS_LOADED = False


DEFAULT_SETTINGS = {
    "theme": "matrix",
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
    "process_update_interval": 0.5,
    "net_max_speed_mbps": 100,
    "last_export_path": "",
    "show_system_processes": False,
    "hide_system_exes": [],
    "taskmgr": {
        "process_limit": 20,
        "exclude_system_apps": True
    },
    "customs": {
        "theme": "matrix",
        "logo_style": "gradient",
        "show_tips": True,
        "show_logo_shadow": True,
        "cursor_style": "block"
    },
    "shortcuts": {
        "Ctrl+L": "/clear",
        "Alt+Q": "/quit",
        "Alt+C": "clear_input",
        "Shift+Up": "history_prev",
        "Shift+Down": "history_next"
    },
    "commands": {
        "vscode": "code .",
        "ll": "ls -la",
        "grep": "grep --color=auto"
    }
}


def _get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if hasattr(sys, 'argv') and sys.argv and 'app' in sys.argv[0]:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    return base_dir


ROOT_DIR = _get_project_root()


def safe_load_json(path):
    """Read JSON with shared lock - safe for concurrent reads by multiple processes."""
    data = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return data


SETTINGS_PATH = os.path.join(_get_project_root(), "config", "settings.json")


def get_settings():
    global _SETTINGS, _SETTINGS_LOADED
    if _SETTINGS_LOADED and _SETTINGS is not None:
        return _SETTINGS
    
    settings_path = SETTINGS_PATH
    
    loaded_settings = {}
    
    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
        else:
            loaded_settings = DEFAULT_SETTINGS.copy()
    except (json.JSONDecodeError, OSError):
        loaded_settings = DEFAULT_SETTINGS.copy()
    
    _SETTINGS = _merge_with_defaults(loaded_settings)
    _SETTINGS_LOADED = True
    return _SETTINGS


def _merge_with_defaults(loaded: dict) -> dict:
    merged = DEFAULT_SETTINGS.copy()
    if loaded:
        for key, value in loaded.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                merged[key] = {**merged[key], **value}
            else:
                merged[key] = value
    return merged


def reload_settings():
    global _SETTINGS, _SETTINGS_LOADED
    _SETTINGS_LOADED = False
    _SETTINGS = None
    return get_settings()


def _safe_get(data: dict, *keys, default=None):
    result = data
    for key in keys:
        if isinstance(result, dict):
            result = result.get(key)
            if result is None:
                return default
        else:
            return default
    return result if result is not None else default


settings = get_settings()

# ==================== CUSTOMS ====================
customs = _safe_get(settings, "customs") or {}
THEME = _safe_get(customs, "theme", default="matrix")
LOGO_STYLE = _safe_get(customs, "logo_style", default="gradient")
SHOW_TIPS = _safe_get(customs, "show_tips", default=True)
SHOW_LOGO_SHADOW = _safe_get(customs, "show_logo_shadow", default=True)
CURSOR_STYLE = _safe_get(customs, "cursor_style", default="block")

# ==================== SHORTCUTS ====================
shortcuts = _safe_get(settings, "shortcuts") or {}
SHORTCUTS = shortcuts
SHORTCUT_CLEAR = _safe_get(shortcuts, "Ctrl+L", default="/clear")
SHORTCUT_QUIT = _safe_get(shortcuts, "Alt+Q", default="/quit")
SHORTCUT_CLEAR_INPUT = _safe_get(shortcuts, "Alt+C", default="clear_input")
SHORTCUT_HISTORY_PREV = _safe_get(shortcuts, "Shift+Up", default="history_prev")
SHORTCUT_HISTORY_NEXT = _safe_get(shortcuts, "Shift+Down", default="history_next")

# ==================== COMMANDS ====================
commands = _safe_get(settings, "commands") or {}
COMMANDS = commands

# ==================== WINDOW ====================
window_settings = _safe_get(settings, "window_settings") or {}
WINDOW_SETTINGS = window_settings
WINDOW_COLS = _safe_get(window_settings, "cols", default=120)
WINDOW_LINES = _safe_get(window_settings, "lines", default=30)
WINDOW_AUTO_RESIZE = _safe_get(window_settings, "auto_resize", default=True)
WINDOW_FORCE_FULL_WIDTH = _safe_get(window_settings, "force_full_width", default=True)

# ==================== TASK MANAGER ====================
taskmgr_settings = _safe_get(settings, "taskmgr") or {}
TASKMGR_SETTINGS = taskmgr_settings
PROCESS_LIMIT = _safe_get(taskmgr_settings, "process_limit", default=20)
EXCLUDE_SYSTEM_APPS = _safe_get(taskmgr_settings, "exclude_system_apps", default=True)

# ==================== SYSTEM ====================
PROCESS_UPDATE_INTERVAL = _safe_get(settings, "process_update_interval", default=0.5)
REFRESH_INTERVAL = PROCESS_UPDATE_INTERVAL
NET_MAX_SPEED_MBPS = _safe_get(settings, "net_max_speed_mbps", default=100)
SHOW_SYSTEM_PROCESSES = _safe_get(settings, "show_system_processes", default=False)
HIDE_SYSTEM_EXES = _safe_get(settings, "hide_system_exes", default=[])
LAST_EXPORT_PATH = _safe_get(settings, "last_export_path", default="")

# ==================== THEME COLORS (fallbacks) ====================
THEME_COLORS = {
    "primary": "#00FF41",
    "secondary": "#FF00FF",
    "accent": "#00FF41",
    "background": "#0d1117",
    "table_text": "#BBBBBB",
    "table_border": "#444444",
    "header_text": "#000000",
    "error": "#FF0000",
    "success": "#00FF00",
}

def get_theme_primary():
    from functions.theme.theme_logic import get_current_theme_colors
    return get_current_theme_colors().get("primary", THEME_COLORS["primary"])

def get_theme_secondary():
    from functions.theme.theme_logic import get_current_theme_colors
    return get_current_theme_colors().get("secondary", THEME_COLORS["secondary"])

def get_theme_primary_rgb():
    from functions.theme.theme_logic import get_current_theme_colors
    hex_color = get_current_theme_colors().get("primary", THEME_COLORS["primary"])
    if hex_color and len(hex_color) >= 7:
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return r, g, b
        except ValueError:
            pass
    return 0, 255, 65

def get_theme_color(key, default="#c0c0c0"):
    from functions.theme.theme_logic import get_current_theme_colors
    return get_current_theme_colors().get(key, default)

def get_theme_primary_raw():
    from functions.theme.theme_logic import THEMES, current_theme_name, DEFAULT_THEME
    theme = THEMES.get(current_theme_name, THEMES.get(DEFAULT_THEME, THEMES["matrix"]))
    return theme.get("primary", "#00FF41")

def get_theme_secondary_raw():
    from functions.theme.theme_logic import THEMES, current_theme_name, DEFAULT_THEME
    theme = THEMES.get(current_theme_name, THEMES.get(DEFAULT_THEME, THEMES["matrix"]))
    return theme.get("secondary", "#003B00")

def get_theme_bg_raw():
    from functions.theme.theme_logic import THEMES, current_theme_name, DEFAULT_THEME
    theme = THEMES.get(current_theme_name, THEMES.get(DEFAULT_THEME, THEMES["matrix"]))
    return theme.get("background", "#0d1117")

def get_theme_value(key, default="#c0c0c0"):
    from functions.theme.theme_logic import THEMES, current_theme_name, DEFAULT_THEME
    theme = THEMES.get(current_theme_name, THEMES.get(DEFAULT_THEME, THEMES["matrix"]))
    return theme.get(key, default)

def get_colors_dict():
    from functions.theme.theme_logic import get_current_theme_colors
    return get_current_theme_colors()

def get_available_themes():
    from functions.theme.theme_logic import THEMES
    return list(THEMES.keys())


THEME_PRIMARY = get_theme_primary()
THEME_SECONDARY = get_theme_secondary()
THEME_PRIMARY_RGB = get_theme_primary_rgb()
THEME_BG = get_theme_bg_raw()

# ==================== APPLICATION INFO ====================
APP_NAME = "MYCOLOR CLI"
APP_VERSION = "0.0.1"