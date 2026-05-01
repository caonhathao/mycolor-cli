import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import platform
import shutil
import subprocess
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from prompt_toolkit.application import Application
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.widgets import TextArea
from rich.console import Console

from ui.components.input_area import get_input_key_bindings, get_input_text_area
from commands.functions.theme.theme_logic import ensure_config_exists
from core.theme_engine import get_current_theme_colors, get_app_style
from ui.styles.theme_styles import get_theme_style
from core.logger import log_global_crash
from core.constants import APP_VERSION
from ui.screens.cmd_screen import get_cmd_screen_container
from ui.screens.intro_screen import get_intro_screen_container

if TYPE_CHECKING:
    pass

ensure_config_exists()


def _get_settings_path():
    """Get the settings.json path."""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "config", "settings.json")


def set_terminal_title(title: str):
    """Set terminal window title using multiple methods for robustness."""
    # Method 1: ANSI escape sequence (works in Windows Terminal, VT100 compatible)
    sys.stdout.write(f"\x1b]2;{title}\x07")
    sys.stdout.flush()
    
    # Method 2: Windows title command (backup)
    if platform.system() == "Windows":
        os.system(f"title {title}")


def early_window_resize():
    if platform.system() == "Windows":
        try:
            config_path = _get_settings_path()
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


sys.argv = [arg for arg in sys.argv]

mode = "default"
if len(sys.argv) > 1 and "--mode" in sys.argv:
    try:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
    except ValueError:
        pass

early_window_resize()

# Set terminal title immediately on startup
set_terminal_title(f"MYCOLOR - {APP_VERSION}")

async def main_app(mode="default"):
    try:
        reconfig = getattr(sys.stdout, "reconfigure", None)
        if reconfig:
            reconfig(encoding="utf-8")
    except (AttributeError, OSError, ValueError):
        pass

    if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
        try:
            project_directory = os.getcwd()
            app_dir = os.path.join(project_directory, "app")
            myworld_path = os.path.join(app_dir, "myworld.py")
            cmd_args = [
                "wt.exe",
                "-d",
                project_directory,
                sys.executable,
                myworld_path,
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

    if platform.system() == "Windows":
        os.system("mode con: cols=120 lines=30")
        time.sleep(0.2)

    os.system("cls" if os.name == "nt" else "clear")

    console = Console(width=shutil.get_terminal_size().columns)

    # Set terminal window title using ANSI escape sequence
    set_terminal_title(f"MYCOLOR - {APP_VERSION}")

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

    output_buffer = TextArea(
        style="class:output-field", read_only=True, scrollbar=True, focus_on_click=True
    )

    kb = get_input_key_bindings(application, output_buffer)
    application.key_bindings = kb

    app_state: Dict[str, Any] = {"current_screen": "intro" if mode == "default" else mode}
    setattr(application, "app_state", app_state)
    app_state["app_instance"] = application

    def on_input_accept(buff):
        if app_state["current_screen"] == "intro":
            app_state["current_screen"] = "cmd"
            application.renderer.erase()
            application.invalidate()

    text_area = get_input_text_area(
        application, output_buffer, on_accept=on_input_accept
    )

    intro_container = get_intro_screen_container(text_area)
    cmd_container = get_cmd_screen_container(text_area, output_buffer)

    def get_root_container():
        if app_state["current_screen"] == "intro":
            return intro_container
        else:
            return cmd_container

    application.style = get_theme_style()

    root_container = DynamicContainer(get_root_container)

    initial_focus = text_area

    application.layout = Layout(root_container, focused_element=initial_focus)

    with patch_stdout():
        await application.run_async()


if __name__ == "__main__":
    try:
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
        log_global_crash(crash_report)
        print(crash_report, file=sys.stderr)
        input("Press Enter to close...")