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

# Thêm vào sau các dòng import
_notification_trigger = None
_notification_clear = None


def get_cmd_screen_container(input_area, output_buffer):
    """
    Returns the layout container for the Command Screen (OpenCode View).
    Sticky Bottom layout.
    """
    global _notification_trigger, _notification_clear
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

    # --- Notification State ---
    class NotificationState:
        def __init__(self):
            self.show_notification = False
            self.notification_task: asyncio.Task | None = None
            self.notification_message = ""
            self.cached_text = ""
            self.cached_text_hash = 0
            self.cached_lines = []

        def get_sorted_coords(self):
            return None, None

    state = NotificationState()

    def trigger_notification(message, is_success=True):
        """Trigger a notification to display."""

        # Color selection based on status (Theme Integration)
        # Use standard rich colors that align with project classes
        # Success -> Green, Error -> Red
        color = "class:success" if is_success else "class:error"

        # Box Construction
        border = "┃"
        h_padding = "    "  # Exactly 4 spaces horizontal padding

        # Calculate dimensions
        content_len = len(message)
        inner_width = content_len + 8  # 4 spaces left + 4 spaces right

        empty_line = f"{border}{' ' * inner_width}{border}"
        content_line = f"{border}{h_padding}{message}{h_padding}{border}"

        # Construct ANSI string using Rich
        # Exactly 3 lines: Top Padding, Content, Bottom Padding
        box_markup = f"[{color}]{empty_line}\n{content_line}\n{empty_line}[/{color}]"

        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, width=200)
        console.print(box_markup, end="")
        plain_text = buffer.getvalue()
        state.notification_message = plain_text
        state.show_notification = True

        # Persistence with 5s timeout
        async def hide_notification():
            await asyncio.sleep(5)
            state.show_notification = False
            state.notification_message = ""
            get_app().invalidate()

        app = get_app()
        if state.notification_task:
            state.notification_task.cancel()
        state.notification_task = app.create_background_task(hide_notification())

    def clear_notification():
        """Clear the current notification."""
        state.show_notification = False
        state.notification_message = ""

    _notification_trigger = trigger_notification
    _notification_clear = clear_notification
    # Store trigger function globally for access from input_area
    import sys

    _notification_trigger = trigger_notification
    _notification_clear = clear_notification

    # Helper to sync cursor with output_buffer's cursor (allows manual scrolling)
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

    def get_formatted_content():
        import re

        current_text = output_buffer.text
        
        if not current_text:
            return []

        # Logic-Gate: Check cache first
        if current_text == state.cached_text and state.cached_lines:
            return state.cached_lines

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
        state.cached_text = current_text
        state.cached_text_hash = hash(current_text)
        state.cached_lines = formatted
        
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
        count = output_buffer.document.line_count
        return [("fg:ansigreen", f" Buffer: {count}/{MAX_LINES} ")]

    # Wrap in FloatContainer for Completions
    return FloatContainer(
        content=root_split,
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=16, scroll_offset=1),
            ),
            Float(
                right=2,
                top=1,
                content=ConditionalContainer(
                    content=Window(
                        FormattedTextControl(
                            text=lambda: ANSI(state.notification_message)
                        ),
                        height=Dimension(min=1),
                        align=WindowAlign.CENTER,
                    ),
                    filter=Condition(lambda: state.show_notification),
                ),
            ),
        ],
    )


def get_notification_trigger():
    return _notification_trigger


def get_notification_clearer():
    return _notification_clear
