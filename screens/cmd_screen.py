from prompt_toolkit.layout.containers import (
    HSplit,
    VSplit,
    Window,
    FloatContainer,
    Float,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.data_structures import Point
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseEventType

from components.footer import get_footer_container
from components.input_area import RoundedFrame


def get_cmd_screen_container(input_area, output_buffer):
    """
    Returns the layout container for the Command Screen (OpenCode View).
    Sticky Bottom layout.
    """

    # Ensure history is read-only
    output_buffer.read_only = True

    # Helper to sync cursor with output_buffer's cursor (allows manual scrolling)
    def get_buffer_cursor_position():
        return Point(x=0, y=output_buffer.document.cursor_position_row)

    # Mouse handler for history scrolling
    def history_mouse_handler(mouse_event):
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            output_buffer.buffer.cursor_up(count=20)
            return None
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            output_buffer.buffer.cursor_down(count=20)
            return None
        return NotImplemented

    # Output Buffer Window
    history_control = FormattedTextControl(
        text=lambda: ANSI(output_buffer.text),
        get_cursor_position=get_buffer_cursor_position,
    )
    history_control.mouse_handler = history_mouse_handler

    terminal_history = Window(
        content=history_control,
        height=Dimension(weight=1),  # Takes remaining space
        style="class:output-field",
        wrap_lines=True,
        always_hide_cursor=True,
    )

    # Key bindings for scrolling the history
    kb = KeyBindings()

    @kb.add("pageup")
    def _(event):
        output_buffer.buffer.cursor_up(count=10)

    @kb.add("pagedown")
    def _(event):
        output_buffer.buffer.cursor_down(count=10)

    @kb.add(Keys.ScrollUp)
    def _(event):
        output_buffer.buffer.cursor_up(count=5)

    @kb.add(Keys.ScrollDown)
    def _(event):
        output_buffer.buffer.cursor_down(count=5)

    # Content Cluster (Fixed Width 82, Centered to accommodate 80-char box + borders)
    content_cluster = HSplit(
        [
            terminal_history,
            RoundedFrame(input_area, title=""),
        ],
        width=82,
    )

    # Sticky Bottom Layout
    root_split = HSplit(
        [
            VSplit([Window(), content_cluster, Window()]),
            get_footer_container(),
        ],
        style="class:app-background",
        key_bindings=kb,
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
