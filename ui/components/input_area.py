import io
import asyncio
import os
from functools import partial
import hashlib

from rich.console import Console, Group
from rich.text import Text

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.widgets import TextArea, Frame, Label
from prompt_toolkit.layout.containers import (
    Window,
    HSplit,
    VSplit,
    ConditionalContainer,
    DynamicContainer,
)
from prompt_toolkit.filters import Condition, Never, Always
from prompt_toolkit.formatted_text import Template

from commands.registry import dispatch, check_pending_confirmation, is_help_request
from ui.components.completer import DynamicCommandCompleter
from ui.modules.tracker.history_tracker import get_history_tracker
from core.constants import get_theme_primary, get_theme_color, THEME_COLORS

_ANSI_BUFFER = io.StringIO()
_ANSI_CONSOLE = Console(file=_ANSI_BUFFER, force_terminal=True, width=80, color_system="truecolor")
_PLAIN_BUFFER = io.StringIO()
_PLAIN_CONSOLE = Console(file=_PLAIN_BUFFER, force_terminal=True, width=80, color_system=None)


def rich_to_ansi(text):
    """Convert Rich markup string to ANSI escape codes."""
    _ANSI_BUFFER.seek(0)
    _ANSI_BUFFER.truncate(0)
    _ANSI_CONSOLE.print(text, end="")
    return _ANSI_BUFFER.getvalue()


class RoundedBorder:
    HORIZONTAL = "─"
    VERTICAL = "│"
    TOP_LEFT = "╭"
    TOP_RIGHT = "╮"
    BOTTOM_LEFT = "╰"
    BOTTOM_RIGHT = "╯"


class RoundedFrame(Frame):
    def __init__(
        self,
        body,
        title="",
        style="",
        width=None,
        height=None,
        key_bindings=None,
        modal=False,
    ):
        self.title = title
        self.body = body

        fill = partial(Window, style="class:frame.border")
        style = "class:frame " + style

        top_row_with_title = VSplit(
            [
                fill(width=1, height=1, char=RoundedBorder.TOP_LEFT),
                fill(char=RoundedBorder.HORIZONTAL),
                fill(width=1, height=1, char="|"),
                Label(
                    lambda: Template(" {} ").format(self.title),
                    style="class:frame.label",
                    dont_extend_width=True,
                ),
                fill(width=1, height=1, char="|"),
                fill(char=RoundedBorder.HORIZONTAL),
                fill(width=1, height=1, char=RoundedBorder.TOP_RIGHT),
            ],
            height=1,
        )

        top_row_without_title = VSplit(
            [
                fill(width=1, height=1, char=RoundedBorder.TOP_LEFT),
                fill(char=RoundedBorder.HORIZONTAL),
                fill(width=1, height=1, char=RoundedBorder.TOP_RIGHT),
            ],
            height=1,
        )

        @Condition
        def has_title() -> bool:
            return bool(self.title)

        self.container = HSplit(
            [
                ConditionalContainer(
                    content=top_row_with_title,
                    filter=has_title,
                    alternative_content=top_row_without_title,
                ),
                VSplit(
                    [
                        fill(width=1, char=RoundedBorder.VERTICAL),
                        DynamicContainer(lambda: self.body),
                        fill(width=1, char=RoundedBorder.VERTICAL),
                    ],
                    padding=0,
                ),
                VSplit(
                    [
                        fill(width=1, height=1, char=RoundedBorder.BOTTOM_LEFT),
                        fill(char=RoundedBorder.HORIZONTAL),
                        fill(width=1, height=1, char=RoundedBorder.BOTTOM_RIGHT),
                    ],
                    height=1,
                ),
            ],
            width=width,
            height=height,
            style=style,
            key_bindings=key_bindings,
            modal=modal,
        )

    def __pt_container__(self):
        return self.container


def get_input_text_area(application_ref, output_buffer, on_accept=None):
    """
    Returns a configured TextArea widget for the input area.
    Requires a reference to the main prompt_toolkit Application to invalidate it for redraws,
    and a console_ref for printing command output.
    """
    command_completer = DynamicCommandCompleter()

    def log_to_buffer(renderable, save_to_history=True):
        """Renders a Rich object to ANSI string and appends to output buffer."""
        global _ANSI_BUFFER, _ANSI_CONSOLE, _PLAIN_BUFFER, _PLAIN_CONSOLE
        
        _ANSI_BUFFER.seek(0)
        _ANSI_BUFFER.truncate(0)
        
        is_rich_renderable = (
            hasattr(renderable, "__rich_console__") 
            or hasattr(renderable, "__rich__")
            or isinstance(renderable, Group)
        )
        
        if is_rich_renderable:
            _ANSI_CONSOLE.print(renderable)
            ansi_output = _ANSI_BUFFER.getvalue()
            
            if save_to_history:
                _PLAIN_BUFFER.seek(0)
                _PLAIN_BUFFER.truncate(0)
                _PLAIN_CONSOLE.print(renderable)
                plain_text = _PLAIN_BUFFER.getvalue()
                get_history_tracker().append_result(plain_text)
        else:
            _ANSI_CONSOLE.print(str(renderable))
            ansi_output = _ANSI_BUFFER.getvalue()
            
            if save_to_history:
                plain_text = str(renderable)
                get_history_tracker().append_result(plain_text)

        was_read_only = output_buffer.read_only
        output_buffer.read_only = False
        try:
            output_buffer.buffer.cursor_position = len(output_buffer.buffer.text)
            if output_buffer.buffer.text:
                output_buffer.buffer.insert_text("\n")
            output_buffer.buffer.insert_text(ansi_output.rstrip("\n"))
            
            output_buffer.buffer.cursor_position = len(output_buffer.buffer.text)
            
            try:
                from prompt_toolkit.application import get_app
                app = get_app()
                app.layout.focus(output_buffer)
                app.invalidate()
            except Exception:
                pass
        finally:
            output_buffer.read_only = was_read_only

    async def run_system_command(command, log_func, color_hex, app_ref):
        """Executes a system shell command asynchronously and streams output."""
        # Start tracking this command in history
        get_history_tracker().start_new_entry(command)

        try:
            process = await asyncio.create_subprocess_shell(
                command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )

            async def read_stream(stream, is_stderr):
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    try:
                        decoded = line.decode("utf-8").rstrip()
                    except UnicodeDecodeError:
                        decoded = line.decode("cp437", errors="replace").rstrip()

                    if decoded:
                        error_color = get_theme_color("error", "red")
                        style = f"bold {error_color}" if is_stderr else color_hex
                        # Log to buffer and let it handle history capture
                        log_func(f"[{style}]{decoded}[/{style}]", save_to_history=True)
                        app_ref.invalidate()  # Refresh UI instantly for every line

            await asyncio.gather(
                read_stream(process.stdout, False), read_stream(process.stderr, True)
            )
            await process.wait()
        except Exception as e:
            error_color = get_theme_color("error", "red")
            log_func(f"[bold {error_color}]Error executing command: {e}[/bold {error_color}]")

    def accept_input(buff):
        command_text = buff.text.strip()

        if on_accept:
            on_accept(buff)

        from ui.screens.cmd_screen import get_notification_clearer
        clear_notification = get_notification_clearer()
        if clear_notification:
            clear_notification()

        if check_pending_confirmation(command_text, log_to_buffer):
            buff.reset()
            return True

        primary_hex = get_theme_primary()
        suggestion_bg = get_theme_color("suggestion_bg", "#21262d")
        table_text = get_theme_color("table_text", "white")

        if command_text:
            is_help_requested = is_help_request(command_text)
            if not command_text.startswith("/copy") and not is_help_requested:
                get_history_tracker().start_new_entry(command_text)

            history_line = Text()
            history_line.append("▋", style=f"{primary_hex} on {suggestion_bg}")
            history_line.append("  > ", style=f"bold {primary_hex} on {suggestion_bg}")
            history_line.append(command_text, style=f"{table_text} on {suggestion_bg}")
            pad_len = 80 - history_line.cell_len
            if pad_len > 0:
                history_line.append(" " * pad_len, style=f"on {suggestion_bg}")

            padding_line = Text()
            padding_line.append("▋", style=f"{primary_hex} on {suggestion_bg}")
            padding_line.append(" " * 79, style=f"on {suggestion_bg}")

            log_to_buffer(
                Group(padding_line, history_line, padding_line), save_to_history=False
            )

        def _get_notification_trigger():
            from ui.screens.cmd_screen import get_notification_trigger
            return get_notification_trigger()

        notification_trigger = _get_notification_trigger()
        dispatched = dispatch(
            command_text,
            log_to_buffer,
            output_buffer,
            application_ref,
            notification_trigger,
        )

        if not dispatched and command_text:
            if command_text.lower() == "pwd":
                cwd = os.getcwd()
                log_to_buffer(f"[{primary_hex}]{cwd}[/{primary_hex}]")
            elif command_text.lower() == "ls":
                application_ref.create_background_task(
                    run_system_command("dir", log_to_buffer, primary_hex, application_ref)
                )
            elif command_text.lower().startswith("cd"):
                _handle_cd(command_text, log_to_buffer, primary_hex, application_ref)
            else:
                application_ref.create_background_task(
                    run_system_command(
                        command_text, log_to_buffer, primary_hex, application_ref
                    )
                )

        if command_text:
            log_to_buffer("", save_to_history=False)

        if command_text:
            try:
                buff.history.append_string(command_text)
            except Exception:
                pass

        buff.reset()
        return True

    def _handle_cd(command_text, log_to_buffer, primary_hex, app_ref):
        try:
            if (
                command_text.lower() == "cd.."
                or command_text.lower().startswith("cd..\\")
                or command_text.lower().startswith("cd../")
            ):
                target_dir = command_text[2:].strip()
            elif command_text.lower().startswith("cd "):
                target_dir = command_text[3:].strip()
            else:
                if command_text.lower() == "cd":
                    log_to_buffer(f"[{primary_hex}]{os.getcwd()}[/{primary_hex}]")
                    target_dir = None
                else:
                    app_ref.create_background_task(
                        run_system_command(command_text, log_to_buffer, primary_hex, app_ref)
                    )
                    target_dir = None

            if target_dir:
                if (target_dir.startswith('"') and target_dir.endswith('"')) or (
                    target_dir.startswith("'") and target_dir.endswith("'")
                ):
                    target_dir = target_dir[1:-1]

                if target_dir.lower().startswith("/d "):
                    target_dir = target_dir[3:].strip()

                os.chdir(target_dir)
                new_cwd = os.getcwd()
                log_to_buffer(f"[{primary_hex}Changed directory to: {new_cwd}[/{primary_hex}]")
        except Exception as e:
            log_to_buffer(f"[bold red]Error changing directory: {e}[/bold red]")

    history = InMemoryHistory()

    text_area = TextArea(
        multiline=False,
        completer=command_completer,
        complete_while_typing=True,
        accept_handler=accept_input,
        history=history,
        auto_suggest=AutoSuggestFromHistory(),
        prompt=[("class:prompt-prefix", " > ")],
        style="class:input-field",
    )

    # Disable history search on the buffer to fix backspace completion
    if text_area.buffer:
        text_area.buffer.enable_history_search = Never()

    return text_area


def get_input_key_bindings(application_ref, output_buffer=None):
    """Returns key bindings for the main application."""
    kb = KeyBindings()

    @kb.add("c-c", eager=True)
    @kb.add("c-q", eager=True)
    def quit_app(event):
        """Pressing Ctrl-C or Ctrl-Q will exit the user interface."""
        event.app.exit()

    @kb.add("escape", "q")
    def alt_q_quit(event):
        """Alt+Q triggers /quit to exit the application."""
        event.app.exit()

    @kb.add("c-l", eager=True)
    def clear_terminal(event):
        """Ctrl+L triggers /clear command to flush terminal history."""
        if output_buffer:
            dispatch("/clear", lambda x: None, output_buffer, event.app)
            event.app.invalidate()

    @kb.add("escape", "c")
    def alt_c_clear(event):
        """Alt+C clears current input line."""
        event.current_buffer.text = ""
        event.app.invalidate()

    @kb.add("c-v", eager=True)
    def ctrl_v_paste(event):
        """Ctrl+V - Paste from clipboard."""
        try:
            import pyperclip
            clipboard_data = pyperclip.paste()
            if clipboard_data:
                event.current_buffer.insert_text(clipboard_data)
        except Exception:
            pass

    @kb.add("s-up", eager=True)
    def shift_up_history(event):
        """Shift+Up - cycle backward through command history."""
        event.current_buffer.history_backward()
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        event.app.invalidate()

    @kb.add("s-down", eager=True)
    def shift_down_history(event):
        """Shift+Down - cycle forward through command history."""
        event.current_buffer.history_forward()
        event.current_buffer.cursor_position = len(event.current_buffer.text)
        event.app.invalidate()

    return kb
