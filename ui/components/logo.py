from core.logo_engine import get_logo_renderable as engine_get_logo


def get_logo_renderable(width: int, theme=None):
    """
    Thin wrapper around LogoEngine.
    Ignores the passed theme dict; LogoEngine uses get_current_theme_colors() at render time.
    """
    return engine_get_logo(width)
