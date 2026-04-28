import os
import sys

from core.config_manager import get_manager
from core.config_manager import DEFAULT_SETTINGS

def _get_project_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if hasattr(sys, 'argv') and sys.argv and 'app' in sys.argv[0]:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))
    return base_dir

ROOT_DIR = _get_project_root()

config_manager = get_manager()

customs = config_manager.get_customs()
shortcuts = config_manager.get_shortcuts()
commands = config_manager.get_commands()
window_settings = config_manager.get_window()
taskmgr_settings = config_manager.get_taskmgr()

LOGO_STYLE = customs.get("logo_style", "gradient")
SHOW_TIPS = customs.get("show_tips", True)
SHOW_LOGO_SHADOW = customs.get("show_logo_shadow", True)
CURSOR_STYLE = customs.get("cursor_style", "block")

SHORTCUTS = shortcuts
SHORTCUT_CLEAR = shortcuts.get("Ctrl+L", "/clear")
SHORTCUT_QUIT = shortcuts.get("Alt+Q", "/quit")
SHORTCUT_CLEAR_INPUT = shortcuts.get("Alt+C", "clear_input")
SHORTCUT_HISTORY_PREV = shortcuts.get("Shift+Up", "history_prev")
SHORTCUT_HISTORY_NEXT = shortcuts.get("Shift+Down", "history_next")

COMMANDS = commands

WINDOW_SETTINGS = window_settings
WINDOW_COLS = window_settings.get("cols", 120)
WINDOW_LINES = window_settings.get("lines", 30)
WINDOW_AUTO_RESIZE = window_settings.get("auto_resize", True)
WINDOW_FORCE_FULL_WIDTH = window_settings.get("force_full_width", True)

TASKMGR_SETTINGS = taskmgr_settings
PROCESS_LIMIT = taskmgr_settings.get("process_limit", 20)
EXCLUDE_SYSTEM_APPS = taskmgr_settings.get("exclude_system_apps", True)

settings = config_manager.get()

PROCESS_UPDATE_INTERVAL = settings.get("process_update_interval", 0.5)
REFRESH_INTERVAL = PROCESS_UPDATE_INTERVAL
NET_MAX_SPEED_MBPS = settings.get("net_max_speed_mbps", 100)
SHOW_SYSTEM_PROCESSES = settings.get("show_system_processes", False)
HIDE_SYSTEM_EXES = settings.get("hide_system_exes", [])
LAST_EXPORT_PATH = settings.get("last_export_path", "")


def get_theme_primary():
    from core.theme_engine import get_current_theme_colors
    return get_current_theme_colors().get("primary", "#A9B7C6")


def get_theme_secondary():
    from core.theme_engine import get_current_theme_colors
    return get_current_theme_colors().get("secondary", "#CC7832")


def get_theme_primary_rgb():
    from core.theme_engine import get_current_theme_colors
    hex_color = get_current_theme_colors().get("primary", "#A9B7C6")
    if hex_color and len(hex_color) >= 7:
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return r, g, b
        except ValueError:
            pass
    return 169, 183, 198


def get_theme_color(key, default="#c0c0c0"):
    from core.theme_engine import get_current_theme_colors
    return get_current_theme_colors().get(key, default)


def get_colors_dict():
    from core.theme_engine import get_current_theme_colors
    return get_current_theme_colors()


def get_available_themes():
    from core.theme_engine import THEMES
    return list(THEMES.keys())


APP_NAME = "MYCOLOR CLI"
APP_VERSION = "0.0.1"