import io
import asyncio
import os
from functools import partial

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
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import Template

import functions.theme.theme_logic
from functions.theme.theme_cmd import handle_theme_command
from functions.sysinfo.sysinfo_cmd import handle_sysinfo_command
from functions.system.system_cmd import handle_system_command
from functions.help import handle_help_command
from functions.clear import handle_clear_command
from functions.copy.copy_cmd import handle_copy_command
from components.completer import DynamicCommandCompleter
from modules.tracker.history_tracker import get_history_tracker


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


def get_input_text_area(application_ref, console_ref, output_buffer, on_accept=None):
    """
    Returns a configured TextArea widget for the input area.
    Requires a reference to the main prompt_toolkit Application to invalidate it for redraws,
    and a console_ref for printing command output.
    """
    command_completer = DynamicCommandCompleter()

    def log_to_buffer(renderable, save_to_history=True):
        """Renders a Rich object to ANSI string and appends to output buffer."""
        temp_console = Console(file=io.StringIO(), force_terminal=True, width=80)
        temp_console.print(renderable)
        ansi_output = temp_console.file.getvalue().rstrip()

        # Shadow History Capture
        if save_to_history:
            # Render to plain text for history
            txt_console = Console(
                file=io.StringIO(), force_terminal=True, width=80, color_system=None
            )
            txt_console.print(renderable)
            plain_text = txt_console.file.getvalue()
            get_history_tracker().append_result(plain_text)

        # Fix Buffer Clipping: Use insert_text to keep history
        # We need to bypass read_only constraint of the TextArea
        was_read_only = output_buffer.read_only
        output_buffer.read_only = False
        try:
            output_buffer.buffer.cursor_position = len(output_buffer.buffer.text)
            if output_buffer.buffer.text:
                output_buffer.buffer.insert_text("\n")
            output_buffer.buffer.insert_text(ansi_output)
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
                        style = "bold red" if is_stderr else color_hex
                        # Log to buffer and let it handle history capture
                        log_func(f"[{style}]{decoded}[/{style}]", save_to_history=True)
                        app_ref.invalidate()  # Refresh UI instantly for every line

            await asyncio.gather(
                read_stream(process.stdout, False), read_stream(process.stderr, True)
            )
            await process.wait()
        except Exception as e:
            log_func(f"[bold red]Error executing command: {e}[/bold red]")

    def accept_input(buff):
        command_text = buff.text.strip()

        # Notify external listener (e.g. for screen switching)
        if on_accept:
            on_accept(buff)

        # Clear any persistent notifications from previous commands
        from screens.cmd_screen import get_notification_clearer

        clear_notification = get_notification_clearer()
        if clear_notification:
            clear_notification()

        # Fetch dynamic colors for semantic highlighting
        primary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["primary"]
        )

        if command_text:
            # Check if this is a help request (should not be recorded in history)
            is_help_request = (
                (
                    command_text.startswith("/theme")
                    and (
                        " -h " in command_text
                        or command_text.endswith(" -h")
                        or " --help" in command_text
                        or command_text.endswith(" --help")
                    )
                )
                or (
                    command_text.startswith("/system")
                    and (
                        " -h " in command_text
                        or command_text.endswith(" -h")
                        or " --help" in command_text
                        or command_text.endswith(" --help")
                    )
                )
                or (
                    command_text.startswith("/sysinfo")
                    and (
                        " -h " in command_text
                        or command_text.endswith(" -h")
                        or " --help" in command_text
                        or command_text.endswith(" --help")
                    )
                )
                or (command_text == "/theme -h" or command_text == "/theme --help")
                or (command_text == "/system -h" or command_text == "/system --help")
                or (command_text == "/sysinfo -h" or command_text == "/sysinfo --help")
            )

            # 1. Start History Entry (skip for help requests)
            if not command_text.startswith("/copy") and not is_help_request:
                get_history_tracker().start_new_entry(command_text)

            # Echo the command to history
            # New OpenCode aesthetic: Accent bar + Lighter background

            history_line = Text()
            # Part 1: Accent Bar (Purple on Lighter Gray)
            history_line.append("▋", style=f"{primary_hex} on #21262d")
            # Part 2: Spacing & Prompt (Cyan on Lighter Gray)
            history_line.append("  > ", style="bold cyan on #21262d")
            # Part 3: Command (White on Lighter Gray)
            history_line.append(command_text, style="white on #21262d")
            # Fill remaining width with background color (Total 80 chars)
            pad_len = 80 - history_line.cell_len
            if pad_len > 0:
                history_line.append(" " * pad_len, style="on #21262d")

            # Padding line (top/bottom)
            padding_line = Text()
            padding_line.append("▋", style=f"{primary_hex} on #21262d")
            padding_line.append(" " * 79, style="on #21262d")

            log_to_buffer(
                Group(padding_line, history_line, padding_line), save_to_history=False
            )

        if command_text == "/quit":
            application_ref.exit()
        elif command_text.startswith("/theme"):
            handle_theme_command(command_text, log_to_buffer, application_ref)
        elif command_text.startswith("/sysinfo"):
            handle_sysinfo_command(log_to_buffer, command_text)
        elif command_text.startswith("/system"):
            handle_system_command(log_to_buffer, command_text, application_ref)
        elif command_text == "/help":
            handle_help_command(log_to_buffer)
        elif command_text.startswith("/copy"):
            from screens.cmd_screen import get_notification_trigger

            notification_trigger = get_notification_trigger()
            handle_copy_command(
                command_text,
                partial(log_to_buffer, save_to_history=False),
                output_buffer,
                notification_trigger,
            )
        elif (
            command_text == "/clear"
            or command_text.lower() == "cls"
            or command_text.lower() == "clear"
        ):
            handle_clear_command(output_buffer)
        elif command_text.lower() == "pwd":
            # 1. Internal 'pwd' Handler
            cwd = os.getcwd()
            log_to_buffer(f"[{primary_hex}]{cwd}[/{primary_hex}]")
        elif command_text.lower() == "ls":
            # 3. Extend to Other Common Aliases (ls -> dir)
            application_ref.create_background_task(
                run_system_command("dir", log_to_buffer, primary_hex, application_ref)
            )
        elif command_text.lower().startswith("cd"):
            # 1. Internal 'cd' Handler
            try:
                # Handle 'cd..' case
                if (
                    command_text.lower() == "cd.."
                    or command_text.lower().startswith("cd..\\")
                    or command_text.lower().startswith("cd../")
                ):
                    target_dir = command_text[2:].strip()
                elif command_text.lower().startswith("cd "):
                    target_dir = command_text[3:].strip()
                else:
                    # Fallback for just 'cd' or invalid syntax, let shell handle or ignore
                    if command_text.lower() == "cd":
                        log_to_buffer(f"[{primary_hex}]{os.getcwd()}[/{primary_hex}]")
                        target_dir = None
                    else:
                        # Pass through to system shell if it's something like cda
                        application_ref.create_background_task(
                            run_system_command(
                                command_text,
                                log_to_buffer,
                                primary_hex,
                                application_ref,
                            )
                        )
                        target_dir = None

                if target_dir:
                    # Handle quotes if present
                    if (target_dir.startswith('"') and target_dir.endswith('"')) or (
                        target_dir.startswith("'") and target_dir.endswith("'")
                    ):
                        target_dir = target_dir[1:-1]

                    # Handle /d flag for windows drive change (python os.chdir handles drive change automatically on windows)
                    if target_dir.lower().startswith("/d "):
                        target_dir = target_dir[3:].strip()

                    os.chdir(target_dir)
                    new_cwd = os.getcwd()
                    log_to_buffer(
                        f"[{primary_hex}]Changed directory to: {new_cwd}[/{primary_hex}]"
                    )
            except Exception as e:
                log_to_buffer(f"[bold red]Error changing directory: {e}[/bold red]")
        elif command_text:  # Not empty
            application_ref.create_background_task(
                run_system_command(
                    command_text, log_to_buffer, primary_hex, application_ref
                )
            )

        if command_text:
            # Add exactly ONE empty line of space after the Result/Output
            log_to_buffer("", save_to_history=False)

        # Clear the buffer for the next command
        buff.reset()

        # Invalidate the application to force a redraw
        application_ref.invalidate()

    text_area = TextArea(
        multiline=False,
        completer=command_completer,
        complete_while_typing=True,
        accept_handler=accept_input,
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        prompt=[("class:prompt-prefix", " > ")],
        style="class:input-field",
    )

    return text_area


def get_input_key_bindings(application_ref):
    """Returns key bindings for the main application."""
    kb = KeyBindings()

    @kb.add("c-c", eager=True)
    @kb.add("c-q", eager=True)
    def _(event):
        """Pressing Ctrl-C or Ctrl-Q will exit the user interface."""
        event.app.exit()

    return kb
