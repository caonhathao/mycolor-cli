from prompt_toolkit.styles import Style as PTStyle
from core.theme_engine import get_current_theme_colors, get_pt_color_hex

_current_style = None


def get_theme_style():
    global _current_style
    colors = get_current_theme_colors()
    primary_hex = get_pt_color_hex(colors.get("primary", "#A9B7C6"))
    suggestion_bg = colors.get("suggestion_bg", "#3B3F41")
    background = colors.get("background", "#2B2B2B")
    placeholder = colors.get("placeholder", "#666666")
    dim_text = colors.get("dim_text", "#666666")
    footer_text = colors.get("footer_text", "#444444")
    popup_text = colors.get("popup_text", "#BBBBBB")
    selected_fg = colors.get("selected_fg", "#000000")

    _current_style = PTStyle.from_dict({
        "app-background": f"bg:{background}",
        "output-field": f"bg:{background} fg:{colors.get('table_text', 'white')}",
        "input-field": f"bg:{background} fg:{primary_hex}",
        "input-field text": f"bg:{background} fg:{primary_hex}",
        "input-border": f"fg:{primary_hex} bg:{background}",
        "frame.border": f"fg:{primary_hex} bg:{background}",
        "frame.label": f"fg:{primary_hex}",
        "prompt-prefix": f"fg:{primary_hex} bold",
        "placeholder": f"fg:{placeholder} italic",
        "path": f"bg:{background} fg:{dim_text} italic",
        "sep": f"bg:{background} fg:{footer_text}",
        "pc": f"bg:{background} fg:{dim_text} italic",
        "footer-pad": f"bg:{background}",
        "footer-divider": f"fg:{footer_text}",
        "completion-menu": f"bg:{suggestion_bg}",
        "completion-menu.completion": f"bg:{suggestion_bg} fg:{primary_hex}",
        "completion-menu.completion.current": f"bg:{primary_hex} fg:{selected_fg}",
        "scrollbar": f"bg:{background}",
        "popup-menu": f"bg:{suggestion_bg} fg:{primary_hex}",
        "popup-item": f"fg:{popup_text}",
        "popup-selected": f"bg:{primary_hex} fg:{selected_fg} bold",
        "success": f"fg:{colors.get('success', '#00FF41')}",
        "error": f"fg:{colors.get('error', '#FF0000')}",
        "warning": f"fg:{colors.get('warning', '#FFFF00')}",
    })

    return _current_style


def apply_theme_to_app(app):
    app.style = get_theme_style()
    app.invalidate()