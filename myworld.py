import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from datetime import datetime

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.widgets import TextArea
from rich.console import Console

from components.input_area import get_input_key_bindings, get_input_text_area
from functions.theme.theme_logic import ensure_config_exists, get_app_style, load_config
from layout.taskmgr_layout import get_taskmgr_layout
from screens.cmd_screen import get_cmd_screen_container
from screens.intro_screen import get_intro_screen_container

ensure_config_exists()


def early_window_resize():
    """
    On Windows, attempts to resize the console window based on config.json
    settings before the TUI is drawn.
    """
    if platform.system() == "Windows":
        try:
            from functions.theme.theme_logic import _get_config_path
            config_path = _get_config_path()
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    config = json.load(f)
                    ws = config.get("window_settings", {})
                    cols = ws.get("cols", 120)
                    lines = ws.get("lines", 30)
                    os.system(f"mode con: cols={cols} lines={lines}")
                    time.sleep(0.3)
        except Exception:
            pass


# --- Argument Filter (Prevent Leakage) ---
# Filter out common terminal flags that might leak during relaunch
sys.argv = [arg for arg in sys.argv]

# --- Ultra-Early Window Resize ---
early_window_resize()

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


# --- Main Application Logic (prompt_toolkit) ---
async def main_app(mode="default"):
    # Ensure stdout uses UTF-8 so PowerShell hosts don't mangle Unicode output.
    try:
        reconfig = getattr(sys.stdout, "reconfigure", None)
        if reconfig:
            reconfig(encoding="utf-8")
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
    output_buffer = TextArea(
        style="class:output-field", read_only=True, scrollbar=True, focus_on_click=True
    )

    # Update key bindings with output_buffer after it's created
    kb = get_input_key_bindings(application, output_buffer)
    application.key_bindings = kb

    # State Management
    app_state = {"current_screen": "intro" if mode == "default" else mode}
    setattr(application, "app_state", app_state)

    def on_input_accept(buff):
        """Callback when input is accepted."""
        if app_state["current_screen"] == "intro":
            app_state["current_screen"] = "cmd"
            # Force a redraw to switch layout
            application.renderer.erase()
            application.invalidate()

    text_area = get_input_text_area(
        application, output_buffer, on_accept=on_input_accept
    )

    # Initialize Screens
    intro_container = get_intro_screen_container(text_area)
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
            os.system("mode con: cols=120 lines=30")
            time.sleep(0.3)
            os.system("cls")
            sys.stdout.write("\033[H")
            sys.stdout.flush()

        asyncio.run(main_app(mode=mode))
    except Exception:
        import traceback

        crash_report = (
            f"Crash Report - {datetime.now()}\n"
            f"{'-' * 30}\n"
            f"{traceback.format_exc()}\n"
            f"{'=' * 30}\n\n"
        )

        print(crash_report, file=sys.stderr)
        input("Press Enter to close...")
