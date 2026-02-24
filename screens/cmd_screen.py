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
from prompt_toolkit.formatted_text.utils import fragment_list_to_text
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.data_structures import Point
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseEventType, MouseButton
from prompt_toolkit.filters import Condition

from components.footer import get_footer_container
from components.input_area import RoundedFrame
from utils.clipboard_manager import copy_to_clipboard


def get_cmd_screen_container(input_area, output_buffer):
    """
    Returns the layout container for the Command Screen (OpenCode View).
    Sticky Bottom layout.
    """

    # Ensure history is read-only
    output_buffer.read_only = True

    # --- Selection & Notification State ---
    class SelectionState:
        def __init__(self):
            self.start_coord = None  # (logical_line_idx, logical_col_idx)
            self.end_coord = None
            self.is_selecting = False
            self.cached_text = None
            self.cached_lines = None
            
            # Notification state
            self.show_notification = False
            self.notification_task = None

        def clear(self):
            self.start_coord = None
            self.end_coord = None
            self.is_selecting = False

        def get_sorted_coords(self):
            if not self.start_coord or not self.end_coord:
                return None, None
            if self.start_coord > self.end_coord:
                return self.end_coord, self.start_coord
            return self.start_coord, self.end_coord

    state = SelectionState()
    terminal_window = None  # Reference to the window for render info

    # Helper to sync cursor with output_buffer's cursor (allows manual scrolling)
    def get_buffer_cursor_position():
        return Point(x=0, y=output_buffer.document.cursor_position_row)

    # --- Mouse Handler ---
    def history_mouse_handler(mouse_event):
        # Handle Scrolling
        if mouse_event.event_type == MouseEventType.SCROLL_UP:
            output_buffer.buffer.cursor_up(count=20)
            return None
        elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            output_buffer.buffer.cursor_down(count=20)
            return None
        
        # Handle Selection
        app = get_app()

        # 1. Correct Render Info Access & 2. Prevent Race Conditions
        render_info = terminal_window.render_info
        if not render_info:
            return NotImplemented

        # Map visual coordinates to logical text coordinates
        visual_y = mouse_event.position.y
        visual_x = mouse_event.position.x
        
        if visual_y < len(render_info.displayed_lines):
            logical_line_idx = render_info.displayed_lines[visual_y]
            
            # Calculate logical column (accounting for wrapping)
            # Count how many times this line index appeared above in the current view
            wrap_offset = 0
            for y in range(visual_y - 1, -1, -1):
                if render_info.displayed_lines[y] == logical_line_idx:
                    wrap_offset += 1
                else:
                    break
            
            logical_col_idx = visual_x + (wrap_offset * render_info.window_width)
            current_coord = (logical_line_idx, logical_col_idx)

            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                if mouse_event.button == MouseButton.LEFT:
                    app.layout.focus(terminal_window) # Explicit focus
                    state.is_selecting = True
                    state.start_coord = current_coord
                    state.end_coord = current_coord
                    app.invalidate()
                    return None

            elif mouse_event.event_type == MouseEventType.MOUSE_MOVE:
                if state.is_selecting:
                    state.end_coord = current_coord
                    app.invalidate()
                    return None

            elif mouse_event.event_type == MouseEventType.MOUSE_UP:
                if state.is_selecting:
                    state.is_selecting = False
                    state.end_coord = current_coord
                    app.invalidate()
                    return None
                
                # Right click to copy
                if mouse_event.button == MouseButton.RIGHT and state.start_coord:
                    start, end = state.get_sorted_coords()
                    if start and end and state.cached_lines:
                        # Extract text
                        lines = state.cached_lines
                        selected_text = []
                        
                        for i in range(start[0], min(end[0] + 1, len(lines))):
                            line_frags = lines[i]
                            line_text = fragment_list_to_text(line_frags)
                            
                            s_col = start[1] if i == start[0] else 0
                            e_col = end[1] + 1 if i == end[0] else len(line_text)
                            
                            selected_text.append(line_text[s_col:e_col])
                        
                        full_text = "\n".join(selected_text)
                        copy_to_clipboard(full_text)
                        
                        # Trigger Notification
                        state.show_notification = True
                        state.clear() # Clear selection after copy
                        
                        async def hide_notification():
                            await asyncio.sleep(1.5)
                            state.show_notification = False
                            app.invalidate()

                        if state.notification_task:
                            state.notification_task.cancel()
                        state.notification_task = app.create_background_task(hide_notification())
                        
                        app.layout.focus(input_area) # Return focus to input
                        app.invalidate()
                        return None

        return NotImplemented

    # --- Content Generation with Highlighting ---
    def get_formatted_content():
        # Cache ANSI parsing for performance
        current_text = output_buffer.text
        if state.cached_text != current_text:
            state.cached_text = current_text
            # Optimization: Cache the lines structure to avoid re-splitting on every render
            state.cached_lines = list(split_lines(to_formatted_text(ANSI(current_text))))

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
                    new_fragments.append(("class:selection bg:#333333", text[pre_len:pre_len+mid_len], *rest))
                    
                    if pre_len + mid_len < text_len:
                        new_fragments.append((style, text[pre_len+mid_len:], *rest))
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
        always_hide_cursor=False, # Cursor needed for scrolling sync sometimes, but usually hidden by control
    )
    
    # Assign for mouse handler access
    terminal_window = terminal_history

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
            ),
            Float(
                right=2,
                top=1,
                content=ConditionalContainer(
                    content=Window(
                        FormattedTextControl(lambda: [("bold ansigreen", "Copied to clipboard")]),
                        height=1,
                        align=WindowAlign.CENTER
                    ),
                    filter=Condition(lambda: state.show_notification)
                )
            )
        ],
    )
