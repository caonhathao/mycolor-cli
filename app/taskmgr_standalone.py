import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import platform
import shutil
import time
from datetime import datetime
from typing import Any, Dict

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import ColorDepth
from rich.console import Console

from commands.functions.theme.theme_logic import ensure_config_exists, get_app_style, load_config
from ui.layout.taskmgr_layout import get_taskmgr_layout, get_current_taskmgr_interface
from core.logger import log_global_crash, CrashLogger


_taskmgr_logger = CrashLogger("taskmgr", "standalone")


def early_window_resize():
    if platform.system() == "Windows":
        try:
            os.system("mode con: cols=120 lines=30")
            time.sleep(0.2)
        except Exception:
            pass


def _write_debug_log(message):
    _taskmgr_logger.write(message)


early_window_resize()
ensure_config_exists()
load_config()


async def main_taskmgr():
    if platform.system() == "Windows":
        os.system("cls")

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

    kb = KeyBindings()

    container, focus = get_taskmgr_layout(application)
    interface = get_current_taskmgr_interface()

    if not interface:
        _write_debug_log("ERROR: TaskManagerInterface is None!")
        console.print("[red]Failed to initialize task manager interface.[/red]")
        return

    @kb.add("q", eager=True)
    @kb.add("escape", eager=True)
    def quit_app(event):
        interface.running = False
        event.app.exit()

    @kb.add("left")
    def prev_tab(event):
        interface.switch_tab(-1)

    @kb.add("right")
    def next_tab(event):
        interface.switch_tab(1)

    application.key_bindings = kb

    app_state: Dict[str, Any] = {"current_screen": "taskmgr"}
    setattr(application, "app_state", app_state)
    app_state["app_instance"] = application
    app_state["taskmgr_instance"] = interface

    if interface:
        interface.first_render = True
        application.create_background_task(interface.update_loop())

    application.style = get_app_style()

    root_container = DynamicContainer(lambda: container)
    application.layout = Layout(root_container, focused_element=focus)

    await application.run_async()


if __name__ == "__main__":
    try:
        if platform.system() == "Windows":
            os.system("mode con: cols=120 lines=30")
            time.sleep(0.2)
            os.system("cls")
            sys.stdout.write("\033[H")
            sys.stdout.flush()

        asyncio.run(main_taskmgr())
    except Exception:
        import traceback
        crash_report = (
            f"=== TASK MANAGER CRASH REPORT ===\n"
            f"Time: {datetime.now()}\n"
            f"PID: {os.getpid()}\n"
            f"{'-' * 40}\n"
            f"{traceback.format_exc()}\n"
            f"{'=' * 40}\n\n"
        )
        _taskmgr_logger.log_crash(crash_report)
        log_global_crash(crash_report)