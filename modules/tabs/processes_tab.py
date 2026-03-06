import io
import shutil
from time import time
from typing import Optional

import psutil
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console
from rich.table import Table

from functions.theme.theme_logic import get_current_theme_colors
from .base_tab import BaseTab

PROCESS_UPDATE_INTERVAL = 3.0
UI_OFFSET = 5


class ProcessesTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.processes = []
        self.procs = {}
        self.last_fetch_time = 0
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_rows = 20
        self._data_changed = True

        psutil.cpu_percent(interval=None)

        self._cached_content: Optional[ANSI] = None
        self._cached_content_hash: Optional[tuple] = None
        self._content_buffer: io.StringIO = io.StringIO()
        self._content_console: Console = Console(
            file=self._content_buffer, force_terminal=True, width=120
        )

    def update(self, current_time: float) -> bool:
        if (
            self.last_fetch_time == 0
            or (current_time - self.last_fetch_time) >= PROCESS_UPDATE_INTERVAL
        ):
            self._fetch_processes()
            self.last_fetch_time = current_time
            self._data_changed = True
            return True
        return False

    def _fetch_processes(self):
        current_pids = set()
        process_list = []

        for p in psutil.process_iter(
            [
                "pid",
                "name",
                "cpu_percent",
                "memory_percent",
                "num_threads",
                "create_time",
                "username",
            ]
        ):
            try:
                pid = p.info["pid"]
                current_pids.add(pid)

                # STRICT PRESERVATION: Reuse cached process object if it exists.
                # Never replace - AccessDenied on validation means keep using cached.
                if pid in self.procs:
                    cached_p = self.procs[pid]
                    try:
                        if cached_p.is_running():
                            p = cached_p
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                with p.oneshot():
                    cpu = p.cpu_percent(interval=None)
                    info = p.info.copy()
                    info["cpu_percent"] = min(100.0, max(0.0, cpu))
                    info["num_handles"] = 0
                    try:
                        info["num_handles"] = p.num_handles()
                    except (AttributeError, psutil.AccessDenied):
                        pass

                process_list.append(info)

                # Only cache NEW PIDs - never overwrite existing process objects
                if pid not in self.procs:
                    self.procs[pid] = p

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        dead_pids = set(self.procs.keys()) - current_pids
        for pid in dead_pids:
            del self.procs[pid]

        self.processes = sorted(
            process_list,
            key=lambda x: (x["cpu_percent"], x.get("memory_percent", 0)),
            reverse=True,
        )

    def render(self):
        term_width = shutil.get_terminal_size().columns
        term_height = shutil.get_terminal_size().lines
        self.visible_rows = max(5, term_height - UI_OFFSET)

        cpu_hash = hash(
            tuple(
                (p["pid"], p["cpu_percent"]) for p in self.processes[:50]
            )
        )
        data_hash = (
            len(self.processes),
            self.visible_rows,
            self.selected_index,
            self.scroll_offset,
            cpu_hash,
        )

        if self._cached_content and self._cached_content_hash == data_hash:
            return self._cached_content

        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        secondary_hex = colors["secondary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "white")

        console_width = max(10, term_width - 2)
        self._content_console.width = console_width
        self._content_buffer.seek(0)
        self._content_buffer.truncate(0)

        table = Table(
            show_header=True,
            header_style=f"bold {primary_hex}",
            box=None,
            expand=True,
        )
        table.add_column("PID", width=7, style="dim", no_wrap=True)
        table.add_column("Name", style=table_text, ratio=1)
        table.add_column("User", style=primary_hex, width=12)
        table.add_column("Threads", justify="right", style=secondary_hex, width=7)
        table.add_column("Handles", justify="right", style=secondary_hex, width=7)
        table.add_column("CPU%", justify="right", style=secondary_hex, width=7)
        table.add_column("MEM%", justify="right", style=secondary_hex, width=7)

        current_processes = list(self.processes)
        visible_rows = self.visible_rows
        max_idx = len(current_processes) - 1
        if self.selected_index > max_idx:
            self.selected_index = max_idx

        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_rows:
            self.scroll_offset = self.selected_index - visible_rows + 1

        for i in range(
            self.scroll_offset,
            min(len(current_processes), self.scroll_offset + visible_rows),
        ):
            try:
                p = current_processes[i]
                style = f"on {suggestion_bg}" if i == self.selected_index else ""
                username = p.get("username", "")
                if username:
                    user_short = username.split("\\")[-1][:11]
                else:
                    user_short = ""
                table.add_row(
                    str(p["pid"]),
                    p["name"],
                    user_short,
                    str(p.get("num_threads", 0)),
                    str(p.get("num_handles", 0)),
                    f"{p['cpu_percent']:.1f}",
                    f"{p['memory_percent']:.1f}",
                    style=style,
                )
            except (IndexError, KeyError):
                pass

        self._content_console.print(table)

        self._cached_content = ANSI(self._content_buffer.getvalue())
        self._cached_content_hash = data_hash
        return self._cached_content

    def on_activate(self):
        self._data_changed = True

    def on_deactivate(self):
        pass
