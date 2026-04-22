import asyncio
import os
import platform
import shutil
import sys
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import ColorDepth
from rich.console import Console

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from functions.theme.theme_logic import ensure_config_exists, get_app_style, load_config
from layout.taskmgr_layout import get_taskmgr_layout

if TYPE_CHECKING:
    from screens.taskmgr_screen import TaskManagerInterface


def early_window_resize():
    if platform.system() == "Windows":
        try:
            os.system("mode con: cols=120 lines=30")
            time.sleep(0.2)
        except Exception:
            pass


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
    
    @kb.add("q", eager=True)
    @kb.add("escape", eager=True)
    def quit_app(event):
        event.app.exit()
    
    @kb.add("left")
    def prev_tab(event):
        interface = app_state.get("taskmgr_instance")
        if interface:
            switch_tab = getattr(interface, "switch_tab", None)
            if switch_tab:
                switch_tab(-1)
    
    @kb.add("right")
    def next_tab(event):
        interface = app_state.get("taskmgr_instance")
        if interface:
            switch_tab = getattr(interface, "switch_tab", None)
            if switch_tab:
                switch_tab(1)
    
    application.key_bindings = kb
    
    app_state: Dict[str, Any] = {"current_screen": "taskmgr"}
    setattr(application, "app_state", app_state)
    app_state["app_instance"] = application
    
    taskmgr_container, taskmgr_focus = get_taskmgr_layout(application)
    
    from layout.taskmgr_layout import get_current_taskmgr_interface
    interface = get_current_taskmgr_interface()
    app_state["taskmgr_instance"] = interface
    
    if interface:
        interface.first_render = True
        application.create_background_task(interface.update_loop())
    
    application.style = get_app_style()
    
    root_container = DynamicContainer(lambda: taskmgr_container)
    application.layout = Layout(root_container, focused_element=taskmgr_focus)
    
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
            f"Crash Report - {datetime.now()}\n"
            f"{'-' * 30}\n"
            f"{traceback.format_exc()}\n"
            f"{'=' * 30}\n\n"
        )
        with open("mw_crash.log", "w") as f:
            f.write(crash_report)