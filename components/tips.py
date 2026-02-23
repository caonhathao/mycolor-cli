from rich.text import Text
from rich.style import Style


def get_tips_renderable(console_width: int, theme: dict):
    """Generates the Tips renderable (centered)."""
    background_style = Style(bgcolor=theme["background"])

    def get_theme_style(key: str) -> Style:
        return theme.get(key, Style())

    tips_base = get_theme_style("primary") + background_style
    tips_text_content = Text.assemble(
        (f"Tip: Type '/' to get the suggestion command list.", tips_base),
        style=tips_base,
    )
    return tips_text_content
