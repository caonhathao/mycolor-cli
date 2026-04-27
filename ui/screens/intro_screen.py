import io

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.containers import (
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import CompletionsMenu
from rich.align import Align
from rich.console import Console

from core.theme_engine import get_current_theme
from ui.components.footer import get_footer_container
from ui.components.input_area import RoundedFrame
from ui.components.logo import get_logo_renderable
from ui.components.tips import get_tips_renderable


def rich_to_ansi(renderable, width):
    """Renders a Rich object to an ANSI string."""
    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=width)
    console.print(renderable)
    return buffer.getvalue()


def get_intro_screen_container(input_area):
    """
    Returns the layout container for the Intro Screen (Hero View).
    Uses Double-Spring centering.
    """
    content_width = 100  # Fixed width for content

    def get_logo_text():
        logo_renderable = get_logo_renderable(
            content_width, get_current_theme()
        )
        return ANSI(rich_to_ansi(logo_renderable, content_width))

    def get_tips_text():
        tips_renderable = Align.center(
            get_tips_renderable(get_current_theme())
        )
        return ANSI(rich_to_ansi(tips_renderable, content_width))

    # Content Cluster
    content = HSplit(
        [
            Window(
                content=FormattedTextControl(get_logo_text),
                height=Dimension(preferred=9),
            ),
            Window(
                content=FormattedTextControl(get_tips_text),
                height=Dimension(preferred=3),
            ),
            RoundedFrame(input_area, title=""),
        ],
        width=content_width,
    )

    # Double-Spring Layout for Center
    center_area = VSplit(
        [
            Window(),  # Left Spring
            HSplit(
                [
                    Window(),  # Top Spring
                    content,
                    Window(),  # Bottom Spring
                ]
            ),
            Window(),  # Right Spring
        ]
    )

    # Root HSplit to pin footer
    root_split = HSplit(
        [center_area, get_footer_container()], style="class:app-background"
    )

    # Wrap in FloatContainer for Completions
    return FloatContainer(
        content=root_split,
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=16, scroll_offset=1),
            )
        ],
    )
