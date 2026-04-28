import asyncio
import io
from typing import Optional
from prompt_toolkit.filters import Condition
from prompt_toolkit.layout.containers import ConditionalContainer, Float, Window, WindowAlign
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console
from core.theme_engine import get_current_theme_colors
from prompt_toolkit.application.current import get_app

# Global task reference (outside class to avoid type conflicts)
_notification_task: Optional[asyncio.Task] = None


class NotificationState:
    def __init__(self):
        self.show_notification = False
        self.notification_message = ""


notification_state = NotificationState()


def trigger_notification(message, is_success=True):
    """Trigger a notification to display."""
    if not message or not message.strip():
        # Clear notification if empty message
        notification_state.show_notification = False
        notification_state.notification_message = ""
        try:
            get_app().invalidate()
        except Exception:
            pass
        return

    colors = get_current_theme_colors()
    color = "class:success" if is_success else "class:error"

    border = "\u2503"
    h_padding = "    "

    content_len = len(message)
    inner_width = content_len + 8

    empty_line = f"{border}{' ' * inner_width}{border}"
    content_line = f"{border}{h_padding}{message}{h_padding}{border}"

    box_markup = f"[{color}]{empty_line}\n{content_line}\n{empty_line}[/{color}]"

    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=200)
    console.print(box_markup, end="")
    plain_text = buffer.getvalue()

    notification_state.notification_message = plain_text
    notification_state.show_notification = True

    async def hide_notification():
        await asyncio.sleep(5)
        notification_state.show_notification = False
        notification_state.notification_message = ""
        try:
            get_app().invalidate()
        except Exception:
            pass

    global _notification_task
    app = get_app()
    if _notification_task:
        _notification_task.cancel()
    _notification_task = app.create_background_task(hide_notification())


def get_notification_trigger():
    return trigger_notification


def get_notification_float():
    """Return a Float containing the notification container."""
    def _has_content():
        return bool(notification_state.show_notification and notification_state.notification_message and notification_state.notification_message.strip())

    def _get_content():
        if not _has_content():
            return ANSI("")
        return ANSI(notification_state.notification_message)

    return Float(
        right=2,
        top=1,
        content=ConditionalContainer(
            content=Window(
                content=FormattedTextControl(
                    text=_get_content
                ),
                height=Dimension(min=1),
                align=WindowAlign.CENTER,
            ),
            filter=Condition(_has_content),
        ),
    )
