import io
import shutil

from ui.modules.tabs.base_tab import BaseTab
from rich.console import Console

from core.theme_engine import get_current_theme_colors


class CommandsTab(BaseTab):

    def __init__(self, parent):
        super().__init__(parent)
        self.selected = 0
        self.scroll_offset = 0
        self._ansi_buffer = io.StringIO()
        self._ansi_console = Console(file=self._ansi_buffer, force_terminal=True, width=120, color_system="truecolor")

    def update(self, current_time: float) -> bool:
        return False

    def render(self):
        self._ansi_buffer.seek(0)
        self._ansi_buffer.truncate(0)

        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "#BBBBBB")

        ALIAS_COL = 20
        CMD_COL = 35

        self._ansi_console.print(f"[bold #00FFFF]{'ALIAS':<{ALIAS_COL}}[/][bold white]{'COMMAND':<{CMD_COL}}[/]")
        self._ansi_console.print("[dim]" + "─" * (ALIAS_COL + CMD_COL) + "[/dim]")

        commands = self.parent._settings.get("commands", {})
        items = list(commands.items())

        for i, (alias, cmd) in enumerate(items):
            is_selected = (i == self.selected)
            row = f"[#00FFFF]{alias:<{ALIAS_COL}}[/][{table_text}]{cmd:<{CMD_COL}}[/]"
            if is_selected:
                self._ansi_console.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
            else:
                self._ansi_console.print(row)

        add_row = " < Add New Command > "
        is_add_selected = (self.selected == len(items))
        row = f"[bold {primary_hex}]{add_row:<{ALIAS_COL + CMD_COL}}[/]"
        if is_add_selected:
            self._ansi_console.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
        else:
            self._ansi_console.print(row)

        return self._ansi_buffer.getvalue()

    def move_selection(self, direction):
        commands = self.parent._settings.get("commands", {})
        items = list(commands.items())
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
        commands = self.parent._settings.get("commands", {})
        items = list(commands.items())

        if self.selected == len(items):
            self.parent.popup_mode = True
            self.parent.popup_options = []
            self.parent.popup_title = "ADD NEW COMMAND"
            self.parent.edit_key = ("command", "add")
        elif items:
            idx = self.selected
            key = items[idx][0]
            current = items[idx][1]
            self.parent.edit_mode = True
            self.parent.edit_key = ("commands", idx)
            self.parent.edit_value = current

    def handle_delete(self):
        commands = self.parent._settings.get("commands", {})
        items = list(commands.items())

        if items and self.selected < len(items):
            idx = self.selected
            key = items[idx][0]
            del self.parent._settings["commands"][key]
            self.parent.commands_items = list(self.parent._settings["commands"].items())
            self.selected = min(self.selected, len(self.parent.commands_items) - 1)
            self.parent.save_all()

    def on_activate(self):
        self.selected = 0

    def on_deactivate(self):
        pass
