import asyncio
from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout.containers import (
    HSplit,
    VSplit,
    Window,
    WindowAlign,
    FloatContainer,
    Float,
    ConditionalContainer,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import ANSI, to_formatted_text, split_lines
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.data_structures import Point
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseEventType

from commands.functions.theme.theme_logic import get_current_theme_colors
from prompt_toolkit.filters import Condition
from rich.console import Console
import io
import re

from ui.components.footer import get_footer_container
from ui.components.input_area import RoundedFrame
from ui.layout.notification_layout import get_notification_float


def get_cmd_screen_container(input_area, output_buffer):
    """
    Returns the layout container for the Command Screen (OpenCode View).
    Sticky Bottom layout.
    """
    # Ensure history is read-only
    output_buffer.read_only = True

    # 1. Increase Buffer Limit & Efficiency (Circular Buffer)
    MAX_LINES = 2500

    def enforce_buffer_limit(_=None):
        if output_buffer.document.line_count > MAX_LINES:
            # Efficiently slice the text to keep only the last MAX_LINES
            lines = output_buffer.text.splitlines(keepends=True)
            if len(lines) > MAX_LINES:
                new_text = "".join(lines[-MAX_LINES:])
                # Bypass read_only to update
                output_buffer.buffer.set_document(
                    Document(new_text, cursor_position=len(new_text)),
                    bypass_readonly=True,
                )

    # Hook into text changed event
    output_buffer.buffer.on_text_changed += enforce_buffer_limit

    def get_buffer_cursor_position():
        return Point(x=0, y=output_buffer.document.cursor_position_row)

    # --- Mouse Handler (Scroll Only - Selection Disabled) ---
    def history_mouse_handler(mouse_event):
        # Handle Scrolling Only - Selection and Right-Click Disabled
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            output_buffer.buffer.cursor_up(count=20)
            return None
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            output_buffer.buffer.cursor_down(count=20)
            return None

        # Disable all other mouse interactions (selection, right-click)
        return NotImplemented

    # --- Content Generation with Caching ---
    # Define state variable for caching (separate from notification state)
    class ContentCache:
        def __init__(self):
            self.cached_text = ""
            self.cached_text_hash = 0
            self.cached_lines = []

    content_cache = ContentCache()

    def get_formatted_content():
        import re

        current_text = output_buffer.text
        
        if not current_text:
            return []
        
        # Logic-Gate: Check cache first
        if current_text == content_cache.cached_text and content_cache.cached_lines:
            return content_cache.cached_lines

        # Cache miss: compute expensive conversion
        try:
            if "\x1b[" in current_text:
                formatted = to_formatted_text(ANSI(current_text))
            else:
                formatted = to_formatted_text(current_text)
        except Exception as e:
            plain_text = re.sub(r'\x1b\[[0-9;]*[mK]', '', current_text)
            formatted = to_formatted_text(plain_text)

        # Update cache
        content_cache.cached_text = current_text
        content_cache.cached_text_hash = hash(current_text)
        content_cache.cached_lines = formatted
        
        return formatted

    # Output Buffer Window
    history_control = FormattedTextControl(
        text=get_formatted_content,
        get_cursor_position=get_buffer_cursor_position,
        focusable=True,
    )
    history_control.mouse_handler = history_mouse_handler

    terminal_history = Window(
        content=history_control,
        height=Dimension(weight=1),  # Takes remaining space
        style="class:output-field",
        wrap_lines=True,
        always_hide_cursor=False,  # Cursor needed for scrolling sync sometimes, but usually hidden by control
    )

    # Key bindings for scrolling the history
    kb = KeyBindings()

    @kb.add("tab")
    def _(event):
        pass  # Disable Tab key - prevent focus switching

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

    # Buffer Status Indicator
    def get_buffer_status():
        colors = get_current_theme_colors()
        status_color = colors.get("primary", "#A9B7C6")
        count = output_buffer.document.line_count
        return [(f"fg:{status_color}", f" Buffer: {count}/{MAX_LINES} ")]

    # Wrap in FloatContainer for Completions and Notifications
    return FloatContainer(
        content=root_split,
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=16, scroll_offset=1),
            ),
            get_notification_float(),
        ],
    )
