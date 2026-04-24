import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import functions.theme.theme_logic
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import DynamicContainer, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.output import ColorDepth

TAB_CUSTOM = 0
TAB_SHORTCUTS = 1
TAB_COMMANDS = 2
TAB_NAMES = ["Customs", "Shortcuts", "Commands"]

_current_interface = None


def get_settings_layout(app):
    global _current_interface
    from screens.settings_screen import SettingsInterface
    interface = SettingsInterface(app)
    _current_interface = interface
    container, focus = build_settings_layout(interface)
    return container, focus


def get_current_settings_interface():
    return _current_interface


def build_settings_layout(interface):
    if not hasattr(interface, 'get_header'):
        raise TypeError(f"Expected SettingsInterface, got {type(interface).__name__}. Use get_settings_layout() instead.")
    
    primary_hex = functions.theme.theme_logic.get_pt_color_hex(
        functions.theme.theme_logic.current_theme.get("primary", "#00FF41")
    )
    accent_hex = functions.theme.theme_logic.get_pt_color_hex(
        functions.theme.theme_logic.current_theme.get("primary", "#00FF41")
    )

    kb = KeyBindings()

    header_window = Window(
        content=FormattedTextControl(interface.get_header),
        height=1,
        style=f"bg:{primary_hex}",
        dont_extend_height=True,
    )

    tabs_window = Window(
        content=FormattedTextControl(interface.get_tabs),
        height=1,
        style="class:footer-pad",
    )

    content_window = Window(
        content=FormattedTextControl(interface.get_content, focusable=False),
        style="class:output-field",
        height=Dimension(weight=1),
    )

    hints_window = Window(
        content=FormattedTextControl(interface.get_hints),
        height=2,
        style="class:footer-pad",
    )

    status_window = Window(
        content=FormattedTextControl(interface.get_status_bar),
        height=1,
        style="class:footer-pad",
    )

    root_container = HSplit(
        [
            header_window,
            VSplit([
                Window(width=1, char=" ", style="class:footer-pad"),
                content_window,
                Window(width=1, char=" ", style="class:footer-pad"),
            ]),
            tabs_window,
            hints_window,
            status_window,
        ],
        key_bindings=kb,
        style="class:app-background",
        width=Dimension(min=80),
    )

    return root_container, content_window