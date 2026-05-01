import io
import shutil
import socket
import threading
from typing import Optional, Tuple, Dict, Any

from prompt_toolkit.formatted_text import ANSI, HTML

from core.config_manager import get_manager
from core.theme_engine import get_current_theme_colors
from ui.modules.tabs.settings.general_tab import GeneralTab
from ui.modules.tabs.settings.shortcuts_tab import ShortcutsTab
from ui.modules.tabs.settings.commands_tab import CommandsTab


class SettingsInterface:
    TAB_GENERAL = 0
    TAB_SHORTCUTS = 1
    TAB_COMMANDS = 2

    def __init__(self, app):
        self.app = app
        self.config_manager = get_manager()
        self.active_tab = 0
        self.running = True
        self.edit_mode = False
        self.edit_key: Optional[Tuple[str, Any]] = None
        self.edit_value = ""
        self.pending_changes = {}
        self.terminal_width = shutil.get_terminal_size().columns

        self._settings = self.config_manager.get()
        self._settings_lock = threading.Lock()
        self._data_changed = True

        self.shortcuts_items = list(self._settings.get("shortcuts", {}).items())
        self.commands_items = list(self._settings.get("commands", {}).items())

        self.popup_mode = False
        self.popup_options = []
        self.popup_selected = 0
        self.popup_title = ""
        self.popup_height = 5
        self.listening_mode = False

        self.tabs = {
            self.TAB_GENERAL: GeneralTab(self),
            self.TAB_SHORTCUTS: ShortcutsTab(self),
            self.TAB_COMMANDS: CommandsTab(self),
        }

    def get_header(self):
        colors = get_current_theme_colors()
        primary_hex = colors.get("primary")
        header_text = colors.get("header_text", "white")
        hostname = socket.gethostname()
        mode_suffix = ""
        if self.popup_mode:
            mode_suffix = " - SELECT"
        elif self.listening_mode:
            mode_suffix = " - LISTENING"
        return [(f"bg:{primary_hex} fg:{header_text} bold", f" SETTINGS MANAGER - {hostname}{mode_suffix} ")]

    def get_content(self):
        active_tab = self.tabs[self.active_tab]
        content = active_tab.render()
        return ANSI(content)

    def get_popup_content(self):
        fragments = []
        options = self.popup_options
        if not options:
            colors = get_current_theme_colors()
            error_color = colors.get("error", colors.get("primary", ""))
            fragments.append((f"fg:{error_color}", " [No data available] "))
            fragments.append(("", "\n"))
            return fragments
        colors = get_current_theme_colors()
        bg_color = colors.get("suggestion_bg", colors.get("primary", ""))
        primary_fg = colors.get("primary", "")
        accent = colors.get("active_tab", colors.get("primary", ""))
        for i, option in enumerate(options):
            if i == self.popup_selected:
                style = f"bg:{accent} fg:{bg_color} bold"
            else:
                style = f"bg:{bg_color} fg:{primary_fg}"
            fragments.append((style, f" {option} ".ljust(20)))
            fragments.append(("", "\n"))
        return fragments

    def get_tabs(self):
        colors = get_current_theme_colors()
        primary_hex = colors.get("primary")
        inactive_color = colors.get("inactive_tab", "#888888")
        tab_names = ["General", "Shortcuts", "Commands"]

        parts = []
        for i, tab in enumerate(tab_names):
            if i == self.active_tab:
                parts.append(f'<b><span color="{primary_hex}">[{tab}]</span></b>')
            else:
                parts.append(f'<span color="{inactive_color}">[{tab}]</span>')

        return HTML('  '.join(parts))

    def get_hints(self):
        colors = get_current_theme_colors()
        accent = colors.get("tab_accent", "#CC7832")
        if self.popup_mode:
            return HTML(
                f'<span color="{accent}">[Up/Down]</span> Navigate  |  '
                f'<span color="{accent}">[Enter]</span> Select  |  '
                f'<span color="{accent}">[Esc/Q]</span> Cancel'
            )
        elif self.listening_mode:
            listening_color = colors.get("warning", "#FFFF00")
            return HTML(
                f'<span color="{listening_color}">Listening...</span> Press key combo  |  '
                f'<span color="{accent}">[Esc/Q]</span> Cancel'
            )
        elif self.edit_mode:
            return HTML(
                f'<span color="{accent}">[Up/Down]</span> Navigate  |  '
                f'<span color="{accent}">[Enter]</span> Edit  |  '
                f'<span color="{accent}">[Del]</span> Delete  |  '
                f'<span color="{accent}">[Esc/Q]</span> Cancel'
            )
        else:
            return HTML(
                f'<span color="{accent}">[Left/Right]</span> Switch Tabs  |  '
                f'<span color="{accent}">[Up/Down]</span> Navigate  |  '
                f'<span color="{accent}">[Enter]</span> Edit  |  '
                f'<span color="{accent}">[Del]</span> Delete  |  '
                f'<span color="{accent}">[Q]</span> Quit'
            )

    def get_system_info(self):
        colors = get_current_theme_colors()
        accent = colors.get("tab_accent", colors.get("primary", ""))
        primary = colors.get("primary", "")
        secondary = colors.get("secondary", colors.get("primary", ""))
        if self.edit_mode or self.popup_mode or self.listening_mode:
            edit_color = colors.get("warning", colors.get("secondary", ""))
            return HTML(f'<span color="{edit_color}">EDIT MODE</span>')
        elif self.pending_changes:
            pending_color = colors.get("error", colors.get("secondary", ""))
            return HTML(f'<span color="{pending_color}">{len(self.pending_changes)} changes</span>')
        else:
            hostname = socket.gethostname()
            return HTML(f'<span color="{primary}">E:\\ProjectDev\\cli</span> <span color="{accent}">|</span> <span color="{secondary}">{hostname}</span> <span color="{accent}">|</span> <span color="{primary}">v0.0.1</span>')

    def switch_tab(self, direction):
        if self.popup_mode or self.listening_mode:
            self.cancel_popup()
            return

        old_tab = self.active_tab
        self.active_tab = (self.active_tab + direction) % 3

        if old_tab != self.active_tab:
            self.tabs[old_tab].on_deactivate()
            self.tabs[self.active_tab].on_activate()
            self.reset_selection()

            if self.app:
                self.app.renderer.clear()
                self.app.invalidate()

    def reset_selection(self):
        self.edit_mode = False
        self.edit_key = None
        self.edit_value = ""
        self.popup_mode = False
        self.popup_selected = 0
        self.popup_options = []

    def move_selection(self, direction):
        if self.popup_mode:
            if self.popup_options:
                self.popup_selected = (self.popup_selected + direction) % len(self.popup_options)
            self._data_changed = True
            if self.app:
                self.app.invalidate()
            return

        if self.edit_mode:
            return

        active_tab = self.tabs[self.active_tab]
        active_tab.move_selection(direction)
        self._data_changed = True

    def handle_enter(self):
        if self.popup_mode:
            self.confirm_popup()
            return

        if self.listening_mode:
            return

        active_tab = self.tabs[self.active_tab]
        active_tab.handle_enter()

    def handle_delete(self):
        if self.popup_mode:
            self.cancel_popup()
            return

        active_tab = self.tabs[self.active_tab]
        active_tab.handle_delete()

    def confirm_popup(self) -> bool:
        edit_key = self.edit_key
        if not isinstance(edit_key, tuple):
            return False

        category = edit_key[0]
        key = edit_key[1]

        if category == "custom":
            options = self.popup_options
            selected_value = options[self.popup_selected]
            self._settings["customs"][key] = selected_value
            self.save_all()
        elif category == "command":
            if key == "add":
                alias = "new_alias"
                cmd = "new_command"
                self._settings["commands"][alias] = cmd
                self.commands_items = list(self._settings["commands"].items())
                self.save_all()

        self.cancel_popup()
        self._notify_restart_required()
        return True

    def cancel_popup(self):
        self.popup_mode = False
        self.listening_mode = False
        self.popup_options = []
        self.popup_selected = 0
        self.edit_key = None
        self._data_changed = True

    def capture_key_combo(self, key_name):
        return self.tabs[self.TAB_SHORTCUTS].capture_key_combo(key_name)

    def update_edit_value(self, char):
        self.edit_value += char
        self._data_changed = True

    def backspace_edit_value(self):
        if self.edit_value:
            self.edit_value = self.edit_value[:-1]
            self._data_changed = True

    def confirm_edit(self):
        if self.edit_mode and self.edit_key:
            edit_key = self.edit_key
            if not isinstance(edit_key, tuple):
                return
            category = edit_key[0]
            key_or_idx = edit_key[1]

            if category == "shortcuts" and isinstance(key_or_idx, int):
                idx = key_or_idx
                key = self.shortcuts_items[idx][0]
                self._settings["shortcuts"][key] = self._ensure_safe_command(self.edit_value)
                self.shortcuts_items = list(self._settings["shortcuts"].items())
            elif category == "commands" and isinstance(key_or_idx, int):
                idx = key_or_idx
                key = self.commands_items[idx][0]
                self._settings["commands"][key] = self.edit_value
                self.commands_items = list(self._settings["commands"].items())

            self.edit_mode = False
            self.edit_key = None
            self.edit_value = ""
            self.pending_changes[category] = True
            self.save_all()
            self._notify_restart_required()

        self._data_changed = True

    def cancel_edit(self):
        self.edit_mode = False
        self.edit_key = None
        self.edit_value = ""
        self._data_changed = True

    def _notify_restart_required(self):
        from ui.layout.notification_layout import get_notification_trigger
        trigger = get_notification_trigger()
        if callable(trigger):
            trigger("Settings saved! Changes will take effect after restart.", is_success=True)

    def save_all(self):
        with self._settings_lock:
            result = self.config_manager.save(self._settings)
        self.pending_changes.clear()
        self._data_changed = True
        return result

    def has_changes(self):
        return bool(self.pending_changes)

    def _ensure_safe_command(self, cmd):
        if not cmd:
            return ""
        if cmd.startswith("/") or cmd in ("clear_input", "history_prev", "history_next"):
            return cmd
        return cmd

if __name__ == "__main__":
    pass
