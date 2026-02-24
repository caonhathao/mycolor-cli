import os
import sys
import json
import time
import platform

# --- Argument Filter (Prevent Leakage) ---
# Filter out common terminal flags that might leak during relaunch
sys.argv = [arg for arg in sys.argv]

# --- Ultra-Early Window Resize ---
if platform.system() == "Windows":
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config.json")
        with open(config_path, "r") as f:
            config = json.load(f)
            ws = config.get("window_settings", {})
            cols = ws.get("cols", 120)
            lines = ws.get("lines", 30)
            os.system(f"mode con: cols={cols} lines={lines}")
            time.sleep(0.3) # Allow buffer to settle
    except Exception:
        pass

import io
import shutil
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
from functions.theme.theme_logic import load_config, current_window_settings, get_app_style

# --- Early Startup Logic ---
# 1. Parse Mode
mode = "default"
if len(sys.argv) > 1 and "--mode" in sys.argv:
    try:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
    except ValueError:
        pass

# 2. Load Config & Resize Terminal
load_config()


from screens.intro_screen import get_intro_screen_container
from screens.cmd_screen import get_cmd_screen_container
from layout.taskmgr_layout import get_taskmgr_layout

# --- Configuration ---
APP_LOG = "app_session.log"

def rich_to_ansi(renderable, width):
    """Renders a Rich object to an ANSI string."""
    console = Console(file=io.StringIO(), force_terminal=True, width=width)
    console.print(renderable)
    return console.file.getvalue()


# --- Main Application Logic (prompt_toolkit) ---
async def main_app(mode="default"):
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
            cmd_args = [
                "wt.exe",
                "-d",
                project_directory,
                sys.executable,
                "myworld.py",
            ]
            if mode != "default":
                cmd_args.extend(["--mode", mode])
            
            subprocess.Popen(cmd_args)
            sys.exit(0)
        except FileNotFoundError:
            print(
                "Windows Terminal (wt.exe) not found. Falling back to current terminal. ANSI colors may not display correctly."
            )
            time.sleep(3)
        except Exception as e:
            print(f"Error relaunching in Windows Terminal: {e}")
            time.sleep(3)

    # Force window size again to stabilize TUI buffer in WT
    if platform.system() == "Windows":
        os.system("mode con: cols=120 lines=30")
        time.sleep(0.2)

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
    app_state = {"current_screen": "intro" if mode == "default" else mode}
    application.app_state = app_state # Attach to app for access in commands

    def on_input_accept(buff):
        """Callback when input is accepted."""
        if app_state["current_screen"] == "intro":
            app_state["current_screen"] = "cmd"
            # Force a redraw to switch layout
            application.renderer.erase()
            application.invalidate()

    text_area = get_input_text_area(application, console, output_buffer, on_accept=on_input_accept)
    
    # Initialize Screens
    intro_container = get_intro_screen_container(text_area, console)
    cmd_container = get_cmd_screen_container(text_area, output_buffer)
    taskmgr_container, taskmgr_focus = get_taskmgr_layout(application)

    def get_root_container():
        if app_state["current_screen"] == "intro":
            return intro_container
        elif app_state["current_screen"] == "taskmgr":
            return taskmgr_container
        else:
            return cmd_container

    application.style = get_app_style()

    # Use DynamicContainer to switch between screens
    root_container = DynamicContainer(get_root_container)
    
    initial_focus = text_area
    if mode == "taskmgr":
        initial_focus = taskmgr_focus
    
    # Force verify initial_focus is a Window
    application.layout = Layout(root_container, focused_element=initial_focus)

    with patch_stdout():
        await application.run_async()


if __name__ == "__main__":
    try:
        # --- Ultimate Terminal Reset ---
        if platform.system() == "Windows":
            os.system('mode con: cols=120 lines=30')
            time.sleep(0.3)
            os.system('cls')
            sys.stdout.write("\033[H")
            sys.stdout.flush()

        asyncio.run(main_app(mode=mode))
    except Exception:
        import traceback

        crash_report = (
            f"Crash Report - {datetime.now()}\n"
            f"{'-' * 30}\n"
            f"{traceback.format_exc()}\n"
            f"{ '=' * 30}\n\n"
        )
        
        print(crash_report, file=sys.stderr)
        input("Press Enter to close...")