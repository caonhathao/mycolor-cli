from prompt_toolkit.layout.containers import HSplit, VSplit, Window, FloatContainer, Float
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.menus import CompletionsMenu
from rich.console import Console
from rich.align import Align
import io

from components.logo import get_logo_renderable
from components.tips import get_tips_renderable
from components.input_area import RoundedFrame
from components.footer import get_footer_container
from functions.theme import current_theme

def rich_to_ansi(renderable, width):
    """Renders a Rich object to an ANSI string."""
    console = Console(file=io.StringIO(), force_terminal=True, width=width)
    console.print(renderable)
    return console.file.getvalue()

def get_intro_screen_container(input_area, console):
    """
    Returns the layout container for the Intro Screen (Hero View).
    Uses Double-Spring centering.
    """
    width = 100 # Fixed width for content
    
    logo_renderable = get_logo_renderable(width, current_theme)
    tips_renderable = Align.center(get_tips_renderable(width, current_theme))
    
    logo_text = ANSI(rich_to_ansi(logo_renderable, width))
    tips_text = ANSI(rich_to_ansi(tips_renderable, width))

    # Content Cluster
    content = HSplit([
        Window(content=FormattedTextControl(lambda: logo_text), height=Dimension(preferred=9)),
        Window(content=FormattedTextControl(lambda: tips_text), height=Dimension(preferred=3)),
        RoundedFrame(input_area, title=""),
    ], width=width)

    # Double-Spring Layout for Center
    center_area = VSplit([
        Window(), # Left Spring
        HSplit([
            Window(), # Top Spring
            content,
            Window()  # Bottom Spring
        ]),
        Window()  # Right Spring
    ])

    # Root HSplit to pin footer
    root_split = HSplit([
        center_area,
        get_footer_container()
    ], style="bg:#0d1117")

    # Wrap in FloatContainer for Completions
    return FloatContainer(
        content=root_split,
        floats=[
            Float(xcursor=True, ycursor=True, content=CompletionsMenu(max_height=16, scroll_offset=1))
        ]
    )