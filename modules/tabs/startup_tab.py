import io
import shutil
from time import time
from typing import Optional

from prompt_toolkit.formatted_text import ANSI
from rich.console import Console
from rich.table import Table

from functions.system.system_logic import get_startup_apps
from functions.theme.theme_logic import get_current_theme_colors
from .base_tab import BaseTab
from ..constants import REFRESH_INTERVAL, get_theme_primary, get_theme_color

STARTUP_UPDATE_INTERVAL: float = 0.5
UI_OFFSET = 5


class StartupTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.startup_apps = []
        self.last_fetch_time = 0
        self.selected_index = 0
        self._data_changed = True

        self._cached_content: Optional[ANSI] = None
        self._cached_content_hash: Optional[tuple] = None
        self._content_buffer: io.StringIO = io.StringIO()
        self._content_console: Console = Console(
            file=self._content_buffer, force_terminal=True, width=120
        )

    def update(self, current_time: float) -> bool:
        if (
            self.last_fetch_time == 0
            or (current_time - self.last_fetch_time) >= STARTUP_UPDATE_INTERVAL
        ):
            self._fetch_startup_apps()
            self.last_fetch_time = current_time
            self._data_changed = True
            return True
        return False

    def _fetch_startup_apps(self):
        self.startup_apps = list(get_startup_apps().items())

    def render(self):
        term_width = shutil.get_terminal_size().columns
        term_height = shutil.get_terminal_size().lines

        data_hash = (
            len(self.startup_apps),
            term_height,
            self.selected_index,
        )

        if self._cached_content and self._cached_content_hash == data_hash:
            return self._cached_content

        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "white")
        success_color = colors.get("success", "green")
        error_color = colors.get("error", "red")

        console_width = max(10, term_width - 2)
        self._content_console.width = console_width
        self._content_buffer.seek(0)
        self._content_buffer.truncate(0)

        if len(self.startup_apps) == 0:
            self._content_console.print(f"[bold {primary_hex}]Startup Applications[/bold {primary_hex}]")
            self._content_console.print("[dim]Loading...[/dim]")
            self._content_console.print("[dim]Press Left/Right to switch tabs[/dim]")
            self._cached_content = ANSI(self._content_buffer.getvalue())
            self._cached_content_hash = data_hash
            return self._cached_content

        table = Table(
            show_header=True,
            header_style=f"bold {primary_hex}",
            box=None,
            expand=True,
        )
        table.add_column("App Name", style=table_text, ratio=1)
        table.add_column("Status", justify="right", width=15)

        for i, (name, info) in enumerate(self.startup_apps):
            style = f"on {suggestion_bg}" if i == self.selected_index else ""
            status = f"[{success_color}]Enabled[/{success_color}]" if info["enabled"] else f"[{error_color}]Disabled[/{error_color}]"
            table.add_row(name, status, style=style)

        self._content_console.print(table)

        self._cached_content = ANSI(self._content_buffer.getvalue())
        self._cached_content_hash = data_hash
        return self._cached_content

    def on_activate(self):
        self._data_changed = True

    def on_deactivate(self):
        self.startup_apps = []
        self._cached_content = None
        self._cached_content_hash = None

    def clear_data(self):
        self.startup_apps = []
        self._cached_content = None
        self._cached_content_hash = None
