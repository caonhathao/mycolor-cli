import psutil  # For /sysinfo command
import io
from functools import partial
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich import box

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.completion import WordCompleter
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

import functions.theme
from functions.theme import set_theme, get_app_style, THEMES


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
    command_completer = WordCompleter(['/theme', '/help', '/sysinfo', '/quit', '/clear'], ignore_case=True)

    def log_to_buffer(renderable):
        """Renders a Rich object to ANSI string and appends to output buffer."""
        temp_console = Console(file=io.StringIO(), force_terminal=True, width=80)
        temp_console.print(renderable)
        ansi_output = temp_console.file.getvalue().rstrip()
        
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

    def accept_input(buff):
        command_text = buff.text.strip()

        # Notify external listener (e.g. for screen switching)
        if on_accept:
            on_accept(buff)

        if command_text:
            # Echo the command to history
            # Boxed command with main theme color
            border_style = functions.theme.current_theme["primary"]
            command_panel = Panel(
                f"[bold cyan] > [/bold cyan]{command_text}",
                box=box.ROUNDED,
                border_style=border_style,
                expand=True, # Expands to console width (80)
                width=80,
                padding=(0, 1)
            )
            log_to_buffer(command_panel)

        if command_text == "/quit":
            application_ref.exit()
        elif command_text.startswith("/theme"):
            parts = command_text.split()
            if len(parts) == 1:
                log_to_buffer("[bold yellow]Usage: /theme [flags][/bold yellow]")
                log_to_buffer("  --style <name>  : Set a specific theme")
                log_to_buffer("  --list          : List available themes")
                log_to_buffer("  --help          : Show detailed help")
            elif len(parts) == 2 and parts[1] == "--help":
                help_content = """
[bold cyan]Description:[/bold cyan]
  Manage the visual theme of the application.

[bold cyan]Flags:[/bold cyan]
  [green]--style <name>[/green]  Apply a specific color theme immediately.
  [green]--list[/green]          Show a table of all available themes.
  [green]--help[/green]          Show this manual.

[bold cyan]Examples:[/bold cyan]
  /theme --style cyber
  /theme --list"""
                log_to_buffer(Panel(help_content.strip(), title="[bold magenta]Command Manual: /theme[/bold magenta]", border_style="cyan"))
            elif len(parts) == 2 and parts[1] == "--list":
                table = Table(title="Available Themes", show_header=False, box=None)
                table.add_column("Name", style="cyan")
                for name in THEMES.keys():
                    table.add_row(name)
                log_to_buffer(table)
            elif len(parts) == 3 and parts[1] == "--style":
                style_name = parts[2]
                if set_theme(style_name):
                    application_ref.style = get_app_style()
                    log_to_buffer(f"[bold green]Theme set to {style_name}[/bold green]")
                else:
                    log_to_buffer(f"[bold red]Error: Theme '{style_name}' not found. Use /theme --list to see options.[/bold red]")
            else:
                log_to_buffer("[bold red]Error: Invalid arguments. Use /theme --help for usage.[/bold red]")
        elif command_text == "/sysinfo":
            try:
                cpu_percent = psutil.cpu_percent(interval=None)  # Non-blocking
                ram_percent = psutil.virtual_memory().percent
                disk_usage = psutil.disk_usage("/").percent
                log_to_buffer(
                    f"[bold blue]System Info:[/bold blue] CPU: {cpu_percent:.1f}% | RAM: {ram_percent:.1f}% | Disk: {disk_usage:.1f}%"
                )
            except Exception as e:
                log_to_buffer(
                    f"[bold red]Error getting system info:[/bold red] {e}"
                )
        elif command_text == "/help":
             log_to_buffer(
                    f"Available commands: /theme, /sysinfo, /quit, /help, /clear"
                )
        elif command_text == "/clear":
             # This is tricky in prompt-toolkit as we don't want to clear the whole screen,
             # just the conceptual "output" area.
             # For now, we can just print a bunch of newlines, or if we had a dedicated output window,
             # we would clear its content. This is a simple placeholder.
             output_buffer.text = ""
        elif command_text: # Not empty
            log_to_buffer(
                f"[bold yellow]Command not recognized:[/bold yellow] {command_text}"
            )
            
        if command_text:
            # Add exactly ONE empty line of space after the Result/Output
            log_to_buffer("")
        
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
