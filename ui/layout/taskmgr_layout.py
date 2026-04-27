from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    DynamicContainer,
    HSplit,
    VSplit,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension

import commands.functions.theme.theme_logic
from ui.screens.taskmgr_screen import TaskManagerInterface

TAB_PROCESSES = 0
REFRESH_INTERVAL = 3.0
_current_interface = None


def get_taskmgr_layout(app):
    """
    Initializes the Task Manager interface and builds the layout.
    Returns (root_container, initial_focus_element).
    """
    global _current_interface
    interface = TaskManagerInterface(app)
    _current_interface = interface
    container, focus = build_taskmgr_layout(interface)
    return container, focus


def get_current_taskmgr_interface():
    """Returns the current TaskManagerInterface instance."""
    return _current_interface


def build_taskmgr_layout(interface):
    # Fetch theme colors
    primary_hex = commands.functions.theme.theme_logic.get_pt_color_hex(
        commands.functions.theme.theme_logic.current_theme["primary"]
    )

    @Condition
    def show_sidebar_condition() -> bool:
        return interface.active_tab == 1 and interface.show_sidebar

    kb = KeyBindings()

    # NOTE: q handler moved to Application-level in myworld.py
    # to ensure it works regardless of focus state

    # --- Layout Components ---

    # 1. Fix Focus Integrity: Create a NON-focusable window for the main content
    content_window = Window(
        content=FormattedTextControl(interface.get_content, focusable=False),
        style="class:output-field",
        height=Dimension(weight=1),
        width=Dimension(weight=1),
    )

    header_window = Window(
        content=FormattedTextControl(interface.get_header),
        height=1,
        style=f"bg:{primary_hex}",
        align=WindowAlign.CENTER,
        dont_extend_height=True,
    )
    
    sidebar_window = Window(
        content=FormattedTextControl(interface.get_sidebar),
        style="class:output-field",
        width=lambda: interface.SIDEBAR_WIDTH,
    )

    # 2. Isolate Footer Keybindings
    tabs_kb = KeyBindings()
    
    # NOTE: left/right handlers moved to Application-level in myworld.py
    # to ensure they work regardless of focus state

    tabs_window = Window(
        content=FormattedTextControl(interface.get_tabs_control, key_bindings=tabs_kb),
        height=1,
        align=WindowAlign.CENTER,
        style="class:footer-pad",
    )
    
    # Link window to interface for focus checking
    interface.tabs_window = tabs_window

    hints_window = Window(
        content=FormattedTextControl(interface.get_hints),
        height=1,
        align=WindowAlign.CENTER,
        style="class:footer-pad",
    )

    status_window = VSplit([
        Window(
            content=FormattedTextControl(interface.get_status_bar),
            height=1,
            align=WindowAlign.RIGHT,
            style="class:footer-pad",
        ),
        Window(width=1, char=" ", style="class:footer-pad")
    ], height=1)

    # --- Performance Tab Layout ---
    # Ensure graphs expand to fill space (weight=1)
    # CRITICAL: Set focusable=False to prevent graph windows from swallowing arrow keys
    cpu_window = Window(content=FormattedTextControl(interface.get_cpu, focusable=False), style="class:output-field", height=Dimension(weight=1), width=Dimension(weight=1))
    ram_window = Window(content=FormattedTextControl(interface.get_ram, focusable=False), style="class:output-field", height=Dimension(weight=1), width=Dimension(weight=1))
    gpu_window = Window(content=FormattedTextControl(interface.get_gpu, focusable=False), style="class:output-field", height=Dimension(weight=1), width=Dimension(weight=1))
    net_window = Window(content=FormattedTextControl(interface.get_network, focusable=False), style="class:output-field", height=Dimension(weight=1), width=Dimension(weight=1))

    col_1_graphs = HSplit([
        cpu_window,
        Window(height=1, char=" "), # Fixed 1-line vertical spacer
        ram_window
    ])

    col_2_graphs = HSplit([
        gpu_window,
        Window(height=1, char=" "), # Fixed 1-line vertical spacer
        net_window
    ])

    graphs_container = VSplit([
        col_1_graphs,
        Window(width=1, char=" "),
        col_2_graphs
    ])

    def get_content_container():
        if interface.active_tab == 1:
            return graphs_container
        else:
            return content_window

    dynamic_content = DynamicContainer(get_content_container)

    # 1. Force Physical Focus - Removed: Direct arrow key navigation now works globally
    # Tab key now disabled to prevent focus trap

    @kb.add("tab")
    def _(event):
        pass  # Disabled: arrow keys now work globally for tab switching

    # 2. Strict 1-Char Spacing: Main VSplit structure
    middle_area = VSplit([
        dynamic_content, # Graphs/List expand to fill space
        Window(width=1, char=" "), # Strict 1-char vertical separator
        ConditionalContainer(
            content=sidebar_window,
            filter=show_sidebar_condition
        ),
        Window(width=1, char=" "), # 1-char safety margin at edge
    ])

    root_container = HSplit(
        [header_window, middle_area, tabs_window, hints_window, status_window],
        key_bindings=kb,
        style="class:app-background",
        width=Dimension(min=100),
    )

    # Return content_window as the initial focus (it's a Window, not a Container)
    return root_container, content_window
