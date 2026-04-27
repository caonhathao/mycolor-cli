import json
import os
import sys

DEFAULT_SETTINGS = {
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


PROJECT_ROOT = _get_project_root()
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
SETTINGS_PATH = os.path.join(CONFIG_DIR, "settings.json")


class ConfigManager:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if ConfigManager._initialized:
            return
        self._settings = None
        self._loaded = False
        ConfigManager._initialized = True
    
    def _load(self):
        if self._loaded and self._settings is not None:
            return self._settings
        
        loaded = {}
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
            else:
                loaded = DEFAULT_SETTINGS.copy()
        except (json.JSONDecodeError, OSError):
            loaded = DEFAULT_SETTINGS.copy()
        
        self._settings = self._merge_with_defaults(loaded)
        self._loaded = True
        return self._settings
    
    def _merge_with_defaults(self, loaded: dict) -> dict:
        merged = DEFAULT_SETTINGS.copy()
        if loaded:
            for key, value in loaded.items():
                if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                    merged[key] = {**merged[key], **value}
                else:
                    merged[key] = value
        return merged
    
    def get(self):
        return self._load()
    
    def reload(self):
        self._loaded = False
        self._settings = None
        return self._load()
    
    def get_nested(self, *keys, default=None):
        data = self.get()
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
                if result is None:
                    return default
            else:
                return default
        return result if result is not None else default
    
    def get_customs(self):
        return self.get_nested("customs") or {}
    
    def get_shortcuts(self):
        return self.get_nested("shortcuts") or {}
    
    def get_commands(self):
        return self.get_nested("commands") or {}
    
    def get_window(self):
        return self.get_nested("window_settings") or {}
    
    def get_taskmgr(self):
        return self.get_nested("taskmgr") or {}
    
    def save(self, data):
        try:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            self._settings = data
            return True
        except OSError:
            return False
    
    def update_section(self, section: str, data: dict):
        current = self.get()
        if section in current:
            current[section].update(data)
        else:
            current[section] = data
        return self.save(current)


_config_manager = ConfigManager()


def get_manager() -> ConfigManager:
    return _config_manager