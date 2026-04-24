import io
import os
import json
import shutil
import re
import threading
from typing import Optional, List, Dict, Any

import psutil
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console

from functions.theme.theme_logic import get_current_theme_colors
from .base_tab import BaseTab
from ..constants import REFRESH_INTERVAL, PROCESS_LIMIT, get_theme_primary, get_theme_secondary, get_theme_color, THEME_COLORS

PROCESS_UPDATE_INTERVAL: float = 0.5
UI_OFFSET = 5

_ANSI_BUFFER = io.StringIO()
_ANSI_CONSOLE = Console(file=_ANSI_BUFFER, force_terminal=True, width=120, color_system="truecolor")

SYSTEM_USERS = {"system", "local service", "network service", "localservice", "networkservice"}
SYSTEM_EXES = {"svchost.exe", "lsass.exe", "lsm.exe", "services.exe", "wininit.exe", 
               "csrss.exe", "smss.exe", "winlogon.exe", "dwm.exe", "explorer.exe"}

COL_WIDTHS = {
    "pid": 8,
    "name": 35,
    "user": 15,
    "threads": 10,
    "handles": 10,
    "cpu": 10,
    "mem": 12,
}


def strip_ansi(text: str) -> str:
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def get_visible_width(text: str) -> int:
    return len(strip_ansi(text))


def truncate_text(text: str, width: int) -> str:
    clean = strip_ansi(text)
    return clean[:width] if len(clean) > width else text


def _load_config() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "config", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {}


class ProcessesTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.processes: List[Dict[str, Any]] = []
        self.procs: Dict[int, Any] = {}
        self.last_fetch_time = 0
        self.selected_index = 0
        self.scroll_offset = 0
        self.visible_rows = 20
        self._data_changed = True
        self._last_config_hash = 0
        self._data_lock = threading.Lock()

        psutil.cpu_percent(interval=None)

        self._cached_content: Optional[ANSI] = None
        self._cached_process_hash: Optional[int] = None

    def update(self, current_time: float) -> bool:
        config = _load_config()
        taskmgr_config = config.get("taskmgr", {})
        show_system = taskmgr_config.get("exclude_system_apps", True)
        
        config_hash = hash(str(show_system))
        
        if (
            self.last_fetch_time == 0
            or (current_time - self.last_fetch_time) >= PROCESS_UPDATE_INTERVAL
            or config_hash != self._last_config_hash
        ):
            with self._data_lock:
                self._fetch_processes(config)
            self.last_fetch_time = current_time
            self._data_changed = True
            self._last_config_hash = config_hash
            return True
        return False

    def _fetch_processes(self, config: Dict[str, Any]):
        process_list: List[Dict[str, Any]] = []
        
        taskmgr_config = config.get("taskmgr", {})
        process_limit = taskmgr_config.get("process_limit", PROCESS_LIMIT)
        show_system = taskmgr_config.get("exclude_system_apps", True)
        
        collected = 0
        skip_system = show_system

        for p in psutil.process_iter(["pid", "name", "username", "exe"]):
            if collected >= process_limit:
                break
            try:
                pid = p.info["pid"]
                name = p.info.get("name", "")
                username = p.info.get("username", "N/A")
                exe_path = p.info.get("exe", "")
                
                if skip_system and exe_path and "C:\\Windows" in exe_path:
                    continue
                    
                info = {
                    "pid": pid,
                    "name": name,
                    "cpu_percent": 0.0,
                    "memory_percent": 0.0,
                    "num_threads": 0,
                    "username": username,
                    "num_handles": 0,
                }
                
                try:
                    with p.oneshot():
                        info["cpu_percent"] = min(100.0, max(0.0, p.cpu_percent(interval=None)))
                        info["memory_percent"] = p.memory_percent()
                        info["num_threads"] = p.num_threads()
                        info["num_handles"] = p.num_handles()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                process_list.append(info)
                collected += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.processes = sorted(process_list, key=lambda x: x["pid"])
        self.procs = {}

    def _format_row(self, pid_str: str, name_str: str, user_str: str, 
                    threads: int, handles: int, cpu_pct: float, mem_pct: float,
                    is_selected: bool, colors: Dict[str, str]) -> str:
        w = COL_WIDTHS
        pid_color = "#00FFFF"
        mem_color = "#00FF88"
        primary_hex = colors["primary"]
        secondary_hex = colors["secondary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "white")

        pid_col = f"[{pid_color}]{pid_str:<{w['pid']}}[/]"
        name_col = f"[{table_text}]{name_str:<{w['name']}}[/]"
        user_col = f"[{primary_hex}]{user_str:<{w['user']}}[/]"
        th_col = f"[{secondary_hex}]{threads:>{w['threads']}}[/]"
        hd_col = f"[{secondary_hex}]{handles:>{w['handles']}}[/]"
        cpu_col = f"[{secondary_hex}]{cpu_pct:>{w['cpu']}.1f}[/]"
        mem_col = f"[{mem_color}]{mem_pct:>{w['mem']}.1f}[/]"

        if is_selected:
            return f"[on {suggestion_bg}]{pid_col}{name_col}{user_col}{th_col}{hd_col}{cpu_col}{mem_col}[/on {suggestion_bg}]"
        return f"{pid_col}{name_col}{user_col}{th_col}{hd_col}{cpu_col}{mem_col}"

    def render(self):
        term_height = shutil.get_terminal_size().lines
        self.visible_rows = max(5, term_height - UI_OFFSET)

        with self._data_lock:
            current_processes = list(self.processes)
        
        visible_rows = self.visible_rows
        total_count = len(current_processes)

        colors = get_current_theme_colors()
        w = COL_WIDTHS

        _ANSI_BUFFER.seek(0)
        _ANSI_BUFFER.truncate(0)

        if total_count == 0:
            header_parts = [
                f"[bold #00FFFF]{'PID':<{w['pid']}}[/]",
                f"[bold white]{'Process Name':<{w['name']}}[/]",
                f"[bold #FFFFFF]{'User':<{w['user']}}[/]",
                f"[bold #00FF88]{'Threads':>{w['threads']}}[/]",
                f"[bold #00FF88]{'Handles':>{w['handles']}}[/]",
                f"[bold #00FF88]{'CPU %':>{w['cpu']}}[/]",
                f"[bold #00FF88]{'Memory %':>{w['mem']}}[/]",
            ]
            _ANSI_CONSOLE.print(" ".join(header_parts))
            _ANSI_CONSOLE.print("[dim]Loading processes...[/dim]")
            _ANSI_CONSOLE.print("[dim]Press Left/Right to switch tabs[/dim]")
            self._cached_content = ANSI(_ANSI_BUFFER.getvalue())
            return self._cached_content

        max_idx = total_count - 1
        if self.selected_index > max_idx:
            self.selected_index = max_idx
        if self.selected_index < 0:
            self.selected_index = 0

        if self.scroll_offset < 0:
            self.scroll_offset = 0
        elif self.scroll_offset > max_idx:
            self.scroll_offset = max_idx

        if self.selected_index < self.scroll_offset:
            self.scroll_offset = self.selected_index
        elif self.selected_index >= self.scroll_offset + visible_rows:
            self.scroll_offset = self.selected_index - visible_rows + 1

        top_50_pids = frozenset(p["pid"] for p in current_processes[:50])
        process_hash = hash((total_count, top_50_pids, self.visible_rows, self.scroll_offset))

        if process_hash == self._cached_process_hash and self._cached_content is not None:
            return self._cached_content

        colors = get_current_theme_colors()
        w = COL_WIDTHS

        _ANSI_BUFFER.seek(0)
        _ANSI_BUFFER.truncate(0)

        header_parts = [
            f"[bold #00FFFF]{'PID':<{w['pid']}}[/]",
            f"[bold white]{'Process Name':<{w['name']}}[/]",
            f"[bold #FFFFFF]{'User':<{w['user']}}[/]",
            f"[bold #00FF88]{'Threads':>{w['threads']}}[/]",
            f"[bold #00FF88]{'Handles':>{w['handles']}}[/]",
            f"[bold #00FF88]{'CPU %':>{w['cpu']}}[/]",
            f"[bold #00FF88]{'Memory %':>{w['mem']}}[/]",
        ]
        header = "".join(header_parts)
        _ANSI_CONSOLE.print(header)

        sep = " " + "-" * (w['pid'] + w['name'] + w['user'] + w['threads'] + w['handles'] + w['cpu'] + w['mem'] + 6)
        _ANSI_CONSOLE.print(f"[dim]{sep}[/dim]")

        start_idx = max(0, min(self.scroll_offset, total_count - 1))
        end_idx = min(total_count, start_idx + visible_rows)

        for row_idx, p in enumerate(current_processes[start_idx:end_idx]):
            actual_idx = start_idx + row_idx
            is_selected = actual_idx == self.selected_index

            try:
                username = p.get("username", "") or ""
                user_short = username.split("\\")[-1][:w['user']]
                name_str = strip_ansi(str(p.get("name", "")))[:w['name']]
                pid_str = str(p["pid"])
                threads = int(p.get("num_threads", 0))
                handles = int(p.get("num_handles", 0))
                cpu_pct = float(p["cpu_percent"])
                mem_pct = float(p["memory_percent"])
            except (KeyError, TypeError, ValueError, AttributeError):
                continue

            row = self._format_row(
                pid_str, name_str, user_short, threads, handles, cpu_pct, mem_pct, is_selected, colors
            )
            _ANSI_CONSOLE.print(row)

        self._cached_content = ANSI(_ANSI_BUFFER.getvalue())
        self._cached_process_hash = process_hash
        return self._cached_content

    def on_activate(self):
        self._data_changed = True

    def on_deactivate(self):
        self.processes = []
        self.procs = {}
        self._cached_content = None
        self._cached_process_hash = None

    def clear_data(self):
        self.processes = []
        self.procs = {}
        self._cached_content = None
        self._cached_process_hash = None
