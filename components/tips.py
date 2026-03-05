from rich.style import Style
from rich.text import Text


def get_tips_renderable(theme: dict):
    """Generates the Tips renderable."""
    primary_style = theme.get("primary", Style())
    background_style = Style(bgcolor=theme.get("background"))
    
    tips_style = primary_style + background_style

    tips_text_content = Text.assemble(
        (
            "Type '/' to get the suggestion command list.\nType '--' to get the suggestion flag list of command.",
            tips_style,
        )
    )
    return tips_text_content
