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
from prompt_toolkit.filters import Condition
from rich.console import Console
import io

from components.footer import get_footer_container
from components.input_area import RoundedFrame
import functions.theme.theme_logic


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

    # --- Notification State ---
    class NotificationState:
        def __init__(self):
            self.show_notification = False
            self.notification_task = None
            self.notification_message = ""
            self.cached_text = ""
            self.cached_lines = []
        
        def get_sorted_coords(self):
            return None, None

    state = NotificationState()
    terminal_window = None  # Reference to the window for render info

    def trigger_notification(message, is_success=True):
        """Trigger a notification to display."""
        
        # Color selection based on status (Theme Integration)
        try:
            # Use standard rich colors that align with project classes
            # Success -> Green, Error -> Red
            color = "class:success" if is_success else "class:error"
        except:
            color = "class:success" if is_success else "class:error"
        
        # Box Construction
        border = "┃"
        h_padding = "    " # Exactly 4 spaces horizontal padding
        
        # Calculate dimensions
        content_len = len(message)
        inner_width = content_len + 8 # 4 spaces left + 4 spaces right
        
        empty_line = f"{border}{' ' * inner_width}{border}"
        content_line = f"{border}{h_padding}{message}{h_padding}{border}"
        
        # Construct ANSI string using Rich
        # Exactly 3 lines: Top Padding, Content, Bottom Padding
        box_markup = f"[{color}]{empty_line}\n{content_line}\n{empty_line}[/{color}]"
        
        console = Console(file=io.StringIO(), force_terminal=True, width=200)
        console.print(box_markup, end="")
        
        state.notification_message = console.file.getvalue()
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

    # Store trigger function globally for access from input_area
    import sys
    sys.modules[__name__]._notification_trigger = trigger_notification
    sys.modules[__name__]._notification_clear = clear_notification

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

    # --- Content Generation with Highlighting ---
    def get_formatted_content():
        # Cache ANSI parsing for performance
        current_text = output_buffer.text
        if state.cached_text != current_text:
            state.cached_text = current_text
            # Optimization: Cache the lines structure to avoid re-splitting on every render
            state.cached_lines = list(
                split_lines(to_formatted_text(ANSI(current_text)))
            )

        lines = state.cached_lines
        start, end = state.get_sorted_coords()

        if not start or not end:
            # Return flattened lines if no selection
            flat_fragments = []
            for line in lines:
                flat_fragments.extend(line)
                flat_fragments.append(("", "\n"))
            if flat_fragments and flat_fragments[-1] == ("", "\n"):
                flat_fragments.pop()
            return flat_fragments

        # Apply highlighting
        new_fragments = []

        # 1. Lines before selection
        for i in range(start[0]):
            new_fragments.extend(lines[i])
            new_fragments.append(("", "\n"))

        # 2. Lines involved in selection
        for i in range(start[0], min(end[0] + 1, len(lines))):
            line = lines[i]
            # Calculate range for this line
            s_col = start[1] if i == start[0] else 0
            e_col = end[1] if i == end[0] else 999999

            # Rebuild line with highlight
            current_col = 0
            for style, text, *rest in line:
                text_len = len(text)
                # Check overlap
                seg_start = current_col
                seg_end = current_col + text_len

                # Intersection logic
                highlight_start = max(seg_start, s_col)
                highlight_end = min(seg_end, e_col + 1)

                if highlight_start < highlight_end:
                    # Split segment
                    pre_len = highlight_start - seg_start
                    mid_len = highlight_end - highlight_start

                    if pre_len > 0:
                        new_fragments.append((style, text[:pre_len], *rest))

                    # Highlighted part (Inverted or Dark Grey bg)
                    new_fragments.append(
                        (
                            "class:selection bg:#333333",
                            text[pre_len : pre_len + mid_len],
                            *rest,
                        )
                    )

                    if pre_len + mid_len < text_len:
                        new_fragments.append((style, text[pre_len + mid_len :], *rest))
                else:
                    new_fragments.append((style, text, *rest))

                current_col += text_len
            new_fragments.append(("", "\n"))

        # 3. Lines after selection
        for i in range(end[0] + 1, len(lines)):
            new_fragments.extend(lines[i])
            new_fragments.append(("", "\n"))

        # Remove last newline added by loop
        if new_fragments and new_fragments[-1] == ("", "\n"):
            new_fragments.pop()

        return new_fragments

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

    # Assign for mouse handler access
    terminal_window = terminal_history

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
            )
        ]
    )


def get_notification_trigger():
    """Returns the notification trigger function from cmd_screen module."""
    import screens.cmd_screen as cmd_module
    if hasattr(cmd_module, '_notification_trigger'):
        return cmd_module._notification_trigger
    return None

def get_notification_clearer():
    """Returns the notification clear function from cmd_screen module."""
    import screens.cmd_screen as cmd_module
    if hasattr(cmd_module, '_notification_clear'):
        return cmd_module._notification_clear
    return None
