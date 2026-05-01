import io
import shutil

from ui.modules.tabs.base_tab import BaseTab
from rich.console import Console

from core.theme_engine import get_current_theme_colors


class ShortcutsTab(BaseTab):

    def __init__(self, parent):
        super().__init__(parent)
        self.selected = 0
        self.scroll_offset = 0
        self.pending_shortcut_key = ""
        self.pending_shortcut_action = ""
        self._ansi_buffer = io.StringIO()
        self._ansi_console = Console(file=self._ansi_buffer, force_terminal=True, width=120, color_system="truecolor")

    def update(self, current_time: float) -> bool:
        return False

    def render(self):
        self._ansi_buffer.seek(0)
        self._ansi_buffer.truncate(0)

        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        secondary = colors.get("secondary", colors.get("primary", ""))
        suggestion_bg = colors.get("suggestion_bg", colors.get("primary", ""))
        table_text = colors.get("table_text", "white")
        accent = colors.get("tab_accent", colors.get("secondary", ""))

        KEY_COL = 20
        ACTION_COL = 30
        DESC_COL = 35

        self._ansi_console.print(f"[bold {secondary}]{'KEY':<{KEY_COL}}[/][bold {table_text}]{'ACTION':<{ACTION_COL}}[/][bold {accent}]{'DESCRIPTION':<{DESC_COL}}[/]")
        self._ansi_console.print("[dim]" + "─" * (KEY_COL + ACTION_COL + DESC_COL) + "[/dim]")

        shortcuts = self.parent._settings.get("shortcuts", {})
        items = list(shortcuts.items())
        descriptions = {
            "/clear": "Clear terminal screen",
            "/quit": "Exit application",
            "clear_input": "Clear command input",
            "history_prev": "Previous command history",
            "history_next": "Next command history",
        }

        for i, (key, action) in enumerate(items):
            is_selected = (i == self.selected)
            desc = descriptions.get(action, "")
            row = f"[{secondary}]{key:<{KEY_COL}}[/][{table_text}]{action:<{ACTION_COL}}[/][{accent}]{desc:<{DESC_COL}}[/]"
            if is_selected:
                self._ansi_console.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
            else:
                self._ansi_console.print(row)

        add_row = " < New Shortcut > "
        is_add_selected = (self.selected == len(items))
        row = f"[bold {primary_hex}]{add_row:<{KEY_COL + ACTION_COL + DESC_COL}}[/]"
        if is_add_selected:
            self._ansi_console.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
        else:
            self._ansi_console.print(row)

        return self._ansi_buffer.getvalue()

    def move_selection(self, direction):
        shortcuts = self.parent._settings.get("shortcuts", {})
        items = list(shortcuts.items())
        max_idx = len(items)
        self.selected = max(0, min(max_idx, self.selected + direction))
        self._update_scroll()

    def _update_scroll(self):
        visible_height = max(5, shutil.get_terminal_size().lines - 10)
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + visible_height:
            self.scroll_offset = self.selected - visible_height + 1

    def handle_enter(self):
        shortcuts = self.parent._settings.get("shortcuts", {})
        items = list(shortcuts.items())

        if self.selected == len(items):
            self.parent.listening_mode = True
            self.parent.pending_shortcut_key = ""
            self.parent.pending_shortcut_action = ""
        elif items:
            idx = self.selected
            key = items[idx][0]
            current = items[idx][1]
            self.parent.edit_mode = True
            self.parent.edit_key = ("shortcuts", idx)
            self.parent.edit_value = current

    def handle_delete(self):
        shortcuts = self.parent._settings.get("shortcuts", {})
        items = list(shortcuts.items())

        if items and self.selected < len(items):
            idx = self.selected
            key = items[idx][0]
            del self.parent._settings["shortcuts"][key]
            self.parent.shortcuts_items = list(self.parent._settings["shortcuts"].items())
            self.selected = min(self.selected, len(self.parent.shortcuts_items) - 1)
            self.parent.save_all()
            self.parent._notify_restart_required()

    def capture_key_combo(self, key_name):
        if self.parent.listening_mode:
            self.parent.pending_shortcut_key = key_name
            self.parent.listening_mode = False

            if self.parent.pending_shortcut_key in self.parent._settings.get("shortcuts", {}):
                return False

            self.parent._settings["shortcuts"][self.parent.pending_shortcut_key] = "custom_action"
            self.parent.shortcuts_items = list(self.parent._settings["shortcuts"].items())
            self.parent.save_all()
            self.parent._notify_restart_required()
            return True
        return False

    def on_activate(self):
        self.selected = 0

    def on_deactivate(self):
        self.parent.listening_mode = False
