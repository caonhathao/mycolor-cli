from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    Float,
    FloatContainer,
    HSplit,
    VSplit,
    Window,
    WindowAlign,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension

from core.theme_engine import get_current_theme_colors

_current_interface = None


def get_settings_layout(app):
    """
    Initializes the Settings interface and builds the layout.
    Returns (root_container, initial_focus_element).
    """
    global _current_interface
    from ui.screens.settings_screen import SettingsInterface
    interface = SettingsInterface(app)
    _current_interface = interface
    container, focus = build_settings_layout(interface)
    return container, focus


def get_current_settings_interface():
    """Returns the current SettingsInterface instance."""
    return _current_interface


def build_settings_layout(interface):
    colors = get_current_theme_colors()
    primary_hex = colors.get("primary")
    
    kb = KeyBindings()

    # 1. Header Window
    header_window = Window(
        content=FormattedTextControl(interface.get_header),
        height=1,
        style=f"bg:{primary_hex}",
        align=WindowAlign.CENTER,
        dont_extend_height=True,
    )

    # 2. Main Content Window - focusable for keyboard navigation
    content_window = Window(
        content=FormattedTextControl(interface.get_content, focusable=True),
        style="class:output-field",
        height=Dimension(weight=1),
        width=Dimension(weight=1),
        dont_extend_width=False,
    )

    # 3. Footer: 3-Layer Vertical Stack (HSplit) - Tabs | Guide | System Info
    footer = HSplit([
        Window(
            content=FormattedTextControl(interface.get_tabs),
            height=1,
            align=WindowAlign.CENTER,
            style="class:footer-pad",
        ),
        Window(
            content=FormattedTextControl(interface.get_hints),
            height=1,
            align=WindowAlign.CENTER,
            style="class:footer-pad",
        ),
        Window(
            content=FormattedTextControl(interface.get_system_info),
            height=1,
            align=WindowAlign.RIGHT,
            style="class:footer-pad",
        ),
    ])

    # Visual separator between content and footer
    divider = Window(height=1, char="─", style="class:footer-divider")

    # Middle Area with 1-char padding
    middle_area = VSplit([
        Window(width=1),
        content_window,
        Window(width=1),
    ])

    # Main HSplit container
    body = HSplit(
        [
            header_window,
            middle_area,
            divider,
            footer,
        ],
        key_bindings=kb,
        style="class:app-background",
        width=Dimension(weight=1),
        height=Dimension(weight=1),
    )

    # Floating Pop-up Menu
    popup_height = interface.popup_height
    popup_window = Window(
        content=FormattedTextControl(interface.get_popup_content, focusable=True),
        style="bg:#21262d",
        width=Dimension(min=1, preferred=20),
        height=Dimension(min=1, preferred=popup_height),
    )

    @Condition
    def show_popup():
        return interface.popup_mode

    # Wrap in ConditionalContainer for filter support
    popup_container = ConditionalContainer(
        content=popup_window,
        filter=show_popup,
    )

    popup_float = Float(
        content=popup_container,
        xcursor=False,
        ycursor=True,
        left=22,
        top=0,
    )

    # Root FloatContainer wrapping HSplit with floats
    root_container = FloatContainer(
        content=body,
        floats=[popup_float],
    )

    return root_container, content_window