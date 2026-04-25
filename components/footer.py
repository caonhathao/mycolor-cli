import os
import socket

from prompt_toolkit.layout.containers import VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl

from modules.constants import get_theme_primary


def get_footer_container():
    """Returns the footer layout container."""
    def get_left_text():
        primary_hex = get_theme_primary()
        return [(f"fg:{primary_hex} bold", os.getcwd())]

    def get_right_text():
        primary_hex = get_theme_primary()
        return [(f"fg:{primary_hex}", f"{socket.gethostname()} | v0.0.1")]

    return VSplit([
        Window(content=FormattedTextControl(get_left_text), align=WindowAlign.LEFT),
        Window(content=FormattedTextControl(get_right_text), align=WindowAlign.RIGHT),
    ], height=1, style="class:footer-pad")