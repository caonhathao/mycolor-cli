from ui.modules.theme_engine import THEMES

def get_available_themes():
    return list(THEMES.keys())

def get_theme_color(theme_name: str, key: str, default: str = "#c0c0c0"):
    theme = THEMES.get(theme_name)
    if theme:
        return theme.get(key, default)
    return default

def get_theme_data(theme_name: str):
    return THEMES.get(theme_name, THEMES.get("matrix"))

def theme_exists(theme_name: str) -> bool:
    return theme_name in THEMES