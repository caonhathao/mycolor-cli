import shutil
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.margins import ScrollbarMargin

from components.footer import get_footer_container
from components.input_area import RoundedFrame
import functions.theme.theme_logic


def get_main_layout(input_area, output_buffer, console):
    """
    Constructs the main application layout.
    """
    # --- Unified History Buffer Logic ---
    ts = shutil.get_terminal_size()
    width = ts.columns

    def get_output_content():
        return ANSI(output_buffer.text)

    terminal_history = Window(
        content=FormattedTextControl(get_output_content),
        height=Dimension(weight=1),  # Flexible height, takes remaining space
        style="class:output-field",
        wrap_lines=True,
        always_hide_cursor=True,
        right_margins=[ScrollbarMargin(display_arrows=True)]
    )

    # Footer - using the container directly
    footer = get_footer_container()

    # --- Sticky Bottom Layout ---
    root_container = HSplit([ 
        terminal_history,
        RoundedFrame(input_area, title="Input"),
        footer
    ], style="class:app-background", width=Dimension(min=width), height=Dimension(min=ts.lines))

    return Layout(root_container, focused_element=input_area)