import os
import sys
import io
import time
import shutil
import platform
import subprocess
from datetime import datetime
import asyncio

from rich.console import Console
from rich.align import Align
from prompt_toolkit.application import Application
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.containers import DynamicContainer

# Custom Modules
from prompt_toolkit.widgets import TextArea
from components.input_area import get_input_text_area, get_input_key_bindings
from functions.theme import load_theme, get_app_style
from screens.intro_screen import get_intro_screen_container
from screens.cmd_screen import get_cmd_screen_container

# --- Configuration ---
LOG_FILE = "mw_crash.log"

def rich_to_ansi(renderable, width):
    """Renders a Rich object to an ANSI string."""
    console = Console(file=io.StringIO(), force_terminal=True, width=width)
    console.print(renderable)
    return console.file.getvalue()


# --- Main Application Logic (prompt_toolkit) ---
async def main_app():
    # Ensure stdout uses UTF-8 so PowerShell hosts don't mangle Unicode output.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        # Older Python or redirected/stdout objects may not support reconfigure.
        pass

    # --- Check for Windows Terminal and Relaunch if necessary ---
    if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
        try:
            project_directory = os.getcwd()
            subprocess.Popen(
                [
                    "wt.exe",
                    "-d",
                    project_directory,
                    "--hold",
                    sys.executable,
                    "myworld.py",
                ]
            )
            sys.exit(0)
        except FileNotFoundError:
            print(
                "Windows Terminal (wt.exe) not found. Falling back to current terminal. ANSI colors may not display correctly."
            )
            time.sleep(3)
        except Exception as e:
            print(f"Error relaunching in Windows Terminal: {e}")
            time.sleep(3)

    # Load theme from config
    load_theme()

    os.system("cls" if os.name == "nt" else "clear")

    console = Console(width=shutil.get_terminal_size().columns)

    application = Application(
        layout=None,
        key_bindings=None,
        full_screen=True,
        mouse_support=True,
        color_depth=ColorDepth.TRUE_COLOR,
        enable_page_navigation_bindings=True,
        style=None,
    )

    kb = get_input_key_bindings(application)
    application.key_bindings = kb

    # --- Unified History Buffer Initialization ---
    # 1. Create the buffer
    output_buffer = TextArea(style="class:output-field", read_only=True, scrollbar=True, focus_on_click=True)

    # State Management
    app_state = {"current_screen": "intro"}

    def on_input_accept(buff):
        """Callback when input is accepted."""
        if app_state["current_screen"] == "intro":
            app_state["current_screen"] = "cmd"
            # Force a redraw to switch layout
            application.invalidate()

    text_area = get_input_text_area(application, console, output_buffer, on_accept=on_input_accept)
    
    # Initialize Screens
    intro_container = get_intro_screen_container(text_area, console)
    cmd_container = get_cmd_screen_container(text_area, output_buffer)

    def get_root_container():
        if app_state["current_screen"] == "intro":
            return intro_container
        else:
            return cmd_container

    application.style = get_app_style()

    # Use DynamicContainer to switch between screens
    root_container = DynamicContainer(get_root_container)
    application.layout = Layout(root_container, focused_element=text_area)

    with patch_stdout():
        await application.run_async()


if __name__ == "__main__":
    # Overwrite log file on each run for clean logs.
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(f"Log started at {datetime.now()}\n")

    try:
        asyncio.run(main_app())
    except Exception:
        import traceback

        crash_report = (
            f"Crash Report - {datetime.now()}\n"
            f"{'-' * 30}\n"
            f"{traceback.format_exc()}\n"
            f"{ '=' * 30}\n\n"
        )
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(crash_report)
        except Exception:
            print(crash_report, file=sys.stderr)