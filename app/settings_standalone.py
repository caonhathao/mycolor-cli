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
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import DynamicContainer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.shortcuts import set_title
from rich.console import Console

from functions.theme.theme_logic import ensure_config_exists, get_app_style, load_config
from layout.settings_layout import build_settings_layout, get_settings_layout, get_current_settings_interface


def early_window_resize():
    if platform.system() == "Windows":
        try:
            os.system("mode con: cols=120 lines=30")
            time.sleep(0.2)
        except Exception:
            pass


def _write_debug_log(message):
    try:
        os.makedirs("logs", exist_ok=True)
        with open("logs/settings_debug.log", "w", encoding="utf-8") as f:
            f.write(f"=== SESSION STARTED: {datetime.now()} | PID: {os.getpid()} ===\n")
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception:
        pass


early_window_resize()
ensure_config_exists()
load_config()


async def main_settings():
    _write_debug_log("main_settings() started")

    set_title("SETTINGS MANAGER")

    if platform.system() == "Windows":
        os.system("cls")

    console = Console(width=shutil.get_terminal_size().columns)

    try:
        application = Application(
            layout=None,
            key_bindings=None,
            full_screen=True,
            mouse_support=True,
            color_depth=ColorDepth.TRUE_COLOR,
            enable_page_navigation_bindings=True,
            style=None,
        )
    except Exception as e:
        _write_debug_log(f"Application creation failed: {e}")
        raise

    kb = KeyBindings()

    try:
        container, focus = get_settings_layout(application)
        _write_debug_log("Layout built successfully")
    except Exception as e:
        _write_debug_log(f"Layout build failed: {e}")
        import traceback
        _write_debug_log(traceback.format_exc())
        raise

    interface = get_current_settings_interface()
    if not interface:
        _write_debug_log("ERROR: SettingsInterface is None!")
        console.print("[red]Failed to initialize settings interface.[/red]")
        return

    @kb.add("q", eager=True)
    @kb.add("escape", eager=True)
    def quit_app(event):
        interface.running = False
        event.app.exit()

    @kb.add("left")
    def prev_tab(event):
        if interface.edit_mode:
            interface.cancel_edit()
        else:
            interface.switch_tab(-1)
            event.app.invalidate()

    @kb.add("right")
    def next_tab(event):
        if interface.edit_mode:
            interface.cancel_edit()
        else:
            interface.switch_tab(1)
            event.app.invalidate()

    @kb.add("up")
    def move_up(event):
        if not interface.edit_mode:
            interface.move_selection(-1)
            event.app.invalidate()

    @kb.add("down")
    def move_down(event):
        if not interface.edit_mode:
            interface.move_selection(1)
            event.app.invalidate()

    @kb.add("enter")
    def handle_enter(event):
        if interface.edit_mode:
            interface.confirm_edit()
            event.app.invalidate()
        else:
            interface.enter_edit_mode()
            event.app.invalidate()

    @kb.add("backspace")
    def handle_backspace(event):
        if interface.edit_mode:
            interface.backspace_edit_value()
            event.app.invalidate()

    @kb.add("c-s")
    def save_settings(event):
        if interface.save_all():
            console.print("[green]Settings saved successfully![/green]")
        else:
            console.print("[red]Failed to save settings.[/red]")

    @kb.add("escape", "s")
    def alt_save_settings(event):
        if interface.save_all():
            console.print("[green]Settings saved successfully![/green]")
        else:
            console.print("[red]Failed to save settings.[/red]")

    @kb.add("escape", "q")
    def alt_quit_no_save(event):
        if interface.has_changes():
            console.print("[yellow]Exiting without saving changes.[/yellow]")
        interface.running = False
        event.app.exit()

    @kb.add("c-q")
    def ctrl_quit_no_save(event):
        if interface.has_changes():
            console.print("[yellow]Exiting without saving changes.[/yellow]")
        interface.running = False
        event.app.exit()

    @kb.add(Keys.Up)
    def handle_up(event):
        if not interface.edit_mode:
            interface.move_selection(-1)
            event.app.invalidate()

    @kb.add(Keys.Down)
    def handle_down(event):
        if not interface.edit_mode:
            interface.move_selection(1)
            event.app.invalidate()

    @kb.add(Keys.Left)
    def handle_left(event):
        if interface.edit_mode:
            interface.cancel_edit()
        else:
            interface.switch_tab(-1)
            event.app.invalidate()

    @kb.add(Keys.Right)
    def handle_right(event):
        if interface.edit_mode:
            interface.cancel_edit()
        else:
            interface.switch_tab(1)
            event.app.invalidate()

    @kb.add(Keys.Enter)
    def handle_enter_key(event):
        if interface.edit_mode:
            interface.confirm_edit()
            event.app.invalidate()
        else:
            interface.enter_edit_mode()
            event.app.invalidate()

    @kb.add(Keys.Backspace)
    def handle_backspace_key(event):
        if interface.edit_mode:
            interface.backspace_edit_value()
            event.app.invalidate()

    @kb.add(Keys.Escape)
    def handle_escape(event):
        if interface.edit_mode:
            interface.cancel_edit()
            event.app.invalidate()
        else:
            interface.running = False
            event.app.exit()

    application.key_bindings = kb

    app_state: Dict[str, Any] = {"current_screen": "settings"}
    setattr(application, "app_state", app_state)
    app_state["app_instance"] = application
    app_state["settings_instance"] = interface

    application.style = get_app_style()

    root_container = DynamicContainer(lambda: container)
    application.layout = Layout(root_container, focused_element=focus)

    try:
        await application.run_async()
    except Exception as e:
        _write_debug_log(f"Application error: {e}")
        import traceback
        _write_debug_log(traceback.format_exc())
        raise


if __name__ == "__main__":
    _write_debug_log("=== Script started ===")
    try:
        asyncio.run(main_settings())
    except Exception:
        import traceback
        crash_report = traceback.format_exc()
        _write_debug_log("CRASH:\n" + crash_report)

        os.makedirs("logs", exist_ok=True)
        with open("logs/mw_crash.log", "w") as f:
            f.write(crash_report)

        print("Settings crashed. Check logs/settings_debug.log for details.")