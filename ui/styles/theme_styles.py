from prompt_toolkit.styles import Style as PTStyle
from core.theme_engine import get_current_theme_colors, get_pt_color_hex

_current_style = None


def get_theme_style():
    global _current_style
    colors = get_current_theme_colors()
    primary_hex = get_pt_color_hex(colors.get("primary", "#A9B7C6"))
    suggestion_bg = colors.get("suggestion_bg", "#3B3F41")
    background = colors.get("background", "#2B2B2B")
    
    _current_style = PTStyle.from_dict({
        "app-background": f"bg:{background}",
        "output-field": f"bg:{background} fg:#ffffff",
        "input-field": f"bg:{background} fg:{primary_hex}",
        "input-field text": f"bg:{background} fg:{primary_hex}",
        "input-border": f"fg:{primary_hex} bg:{background}",
        "frame.border": f"fg:{primary_hex} bg:{background}",
        "frame.label": f"fg:{primary_hex}",
        "prompt-prefix": f"fg:{primary_hex} bold",
        "placeholder": "fg:#666666 italic",
        "path": f"bg:{background} fg:#666666 italic",
        "sep": f"bg:{background} fg:#444444",
        "pc": f"bg:{background} fg:#666666 italic",
        "footer-pad": f"bg:{background}",
        "footer-divider": "fg:#444444",
        "completion-menu": f"bg:{suggestion_bg}",
        "completion-menu.completion": f"bg:{suggestion_bg} fg:{primary_hex}",
        "completion-menu.completion.current": f"bg:{primary_hex} fg:#000000",
        "scrollbar": f"bg:{background}",
        "popup-menu": f"bg:{suggestion_bg} fg:{primary_hex}",
        "popup-item": "fg:#BBBBBB",
        "popup-selected": f"bg:{primary_hex} fg:#000000 bold",
        "success": f"fg:{colors.get('success', '#6A8759')}",
        "error": f"fg:{colors.get('error', '#CC7832')}",
        "warning": f"fg:{colors.get('warning', '#FFFF00')}",
    })
    
    return _current_style


def apply_theme_to_app(app):
    app.style = get_theme_style()
    app.invalidate()