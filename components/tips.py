from rich.style import Style
from rich.text import Text


def get_tips_renderable(theme: dict):
    """Generates the Tips renderable."""
    primary = theme.get("primary")
    background = theme.get("background", "#1c1c1c")
    
    if isinstance(primary, str):
        primary_style = Style(color=primary)
    elif primary is not None and hasattr(primary, "color"):
        primary_style = primary
    else:
        primary_style = Style()
    
    if isinstance(background, str):
        background_style = Style(bgcolor=background)
    else:
        background_style = Style()
    
    tips_style = primary_style + background_style

    tips_text_content = Text.assemble(
        (
            "Type '/' to get the suggestion command list.\nType '--' to get the suggestion flag list of command.",
            tips_style,
        )
    )
    return tips_text_content
