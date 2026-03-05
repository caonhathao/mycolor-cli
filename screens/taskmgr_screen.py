import asyncio
import io
import os
import shutil
import socket
from time import time

import psutil
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console
from rich.table import Table

from functions.system.system_logic import get_startup_apps
from functions.theme.theme_logic import get_current_theme_colors
from modules.monitors.cpu_monitor import CPUMonitor
from modules.monitors.gpu_monitor import GPUMonitor
from modules.monitors.net_monitor import NetMonitor
from modules.monitors.ram_monitor import RAMMonitor
from modules.panel.detail_panel import DetailPanel


class TaskManagerInterface:
    def __init__(self, app):
        self.app = app
        self.active_tab = 0  # 0: Processes, 1: Performance, 2: Startup
        self.focus_mode = "content"  # "content" or "tabs"
        self.selected_index = 0
        self.scroll_offset = 0
        self.processes = []
        self.startup_apps = []
        self.running = True
        self.last_term_size = (0, 0)
        self.first_render = True
        self.tabs_window = None  # Reference to the tabs window for focus checking
        self.last_process_fetch_time = 0
        self.procs = {}  # Cache for Process objects to maintain CPU state

        self.blueprints = {
            "mini": {
                "blocks": {"cpu": {"w": 59, "h": 14}, "details": {"w": 0, "h": 0}},
                "spacers": {"mid_gap": 1, "right_padding": 1},
            },
            "full": {
                "blocks": {"cpu": {"w": 50, "h": 14}, "details": {"w": 22, "h": 28}},
                "spacers": {"mid_gap": 1, "right_padding": 1},
            },
        }
        self.current_mode = "mini"
        self._apply_blueprint(self.current_mode)

        self.FULL_THRESHOLD = 124
        self.show_sidebar = True
        self._load_initial_visibility()

        # Monitors
        self.cpu_monitor = CPUMonitor()
        self.ram_monitor = RAMMonitor()
        self.gpu_monitor = GPUMonitor()
        self.net_monitor = NetMonitor()
        self.detail_panel = DetailPanel()

        self.app.create_background_task(self.update_loop())

    def _load_initial_visibility(self):
        # This is now a dynamic property based on terminal width
        current_width = shutil.get_terminal_size().columns
        self.show_sidebar = current_width >= self.FULL_THRESHOLD

    def _apply_blueprint(self, mode):
        bp = self.blueprints.get(mode, self.blueprints["mini"])
        self.SIDEBAR_WIDTH = bp["blocks"].get("details", {}).get("w", 0)
        self.GRAPH_WIDTH = bp["blocks"]["cpu"]["w"]
        self.GRAPH_HEIGHT = bp["blocks"]["cpu"]["h"]
        self.MID_GAP = bp["spacers"]["mid_gap"]
        self.RIGHT_PADDING = bp["spacers"]["right_padding"]
        self.current_mode = mode

    async def update_loop(self):
        try:
            while self.running:
                current_width = shutil.get_terminal_size().columns
                new_mode = "full" if current_width >= self.FULL_THRESHOLD else "mini"

                if new_mode != self.current_mode:
                    self._apply_blueprint(new_mode)
                    self.show_sidebar = new_mode == "full"
                    self.app.renderer.erase()

                current_term_size = shutil.get_terminal_size()
                if current_term_size != self.last_term_size or self.first_render:
                    self.last_term_size = current_term_size
                    self.first_render = False
                    self.app.renderer.clear()
                    self.app.invalidate()

                if self.app.app_state.get("current_screen") == "taskmgr":
                    current_time = time()

                    if self.active_tab == 1:  # Performance
                        if hasattr(self.gpu_monitor, "resume"):
                            self.gpu_monitor.resume()

                        colors = get_current_theme_colors()
                        secondary_hex = colors["secondary"]

                        self.cpu_monitor.update()
                        self.ram_monitor.update()
                        self.net_monitor.update()
                        self.gpu_monitor.update()

                        width, height = self._calculate_graph_dimensions()
                        self.cpu_monitor.render(
                            width, height, secondary_hex, secondary_hex
                        )
                        self.ram_monitor.render(
                            width, height, secondary_hex, secondary_hex
                        )
                        self.gpu_monitor.render(
                            width, height, secondary_hex, secondary_hex
                        )
                        self.net_monitor.render(
                            width, height, secondary_hex, secondary_hex
                        )

                    else:  # Processes or Startup
                        if hasattr(self.gpu_monitor, "pause"):
                            self.gpu_monitor.pause()

                        if current_time - self.last_process_fetch_time >= 5.0:
                            if self.active_tab == 0:
                                self.fetch_processes()
                            elif self.active_tab == 2:
                                self.startup_apps = list(get_startup_apps().items())
                            self.last_process_fetch_time = current_time

                    if self.show_sidebar:
                        self.detail_panel.update()

                    self.app.invalidate()

                await asyncio.sleep(0.1)
        finally:
            if hasattr(self, "gpu_monitor") and hasattr(self.gpu_monitor, "stop"):
                self.gpu_monitor.stop()
            if hasattr(self, "detail_panel") and hasattr(self.detail_panel, "stop"):
                self.detail_panel.stop()

    def fetch_processes(self):
        cpu_count = psutil.cpu_count() or 1
        new_procs = {}
        process_list = []

        for p in psutil.process_iter(
            [
                "pid",
                "name",
                "cpu_percent",
                "memory_percent",
                "num_threads",
                "create_time",
            ]
        ):
            try:
                if p.pid in self.procs:
                    cached_p = self.procs[p.pid]
                    try:
                        if cached_p.create_time() == p.info["create_time"]:
                            p = cached_p
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                with p.oneshot():
                    cpu = p.cpu_percent(interval=None)
                    normalized_cpu = cpu / cpu_count
                    info = p.info
                    info["cpu_percent"] = normalized_cpu
                    info["num_handles"] = 0
                    try:
                        info["num_handles"] = p.num_handles()
                    except (AttributeError, psutil.AccessDenied):
                        pass

                    process_list.append(info)
                    new_procs[p.pid] = p
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        self.procs = new_procs
        self.processes = sorted(
            process_list, key=lambda x: x["cpu_percent"], reverse=True
        )

    def get_header(self):
        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        hostname = socket.gethostname()
        return [(f"bg:{primary_hex} fg:#000000 bold", f" SYSTEM MONITOR - {hostname} ")]

    def get_sidebar(self):
        return self.detail_panel.render(self.SIDEBAR_WIDTH)

    def _calculate_graph_dimensions(self):
        term_size = shutil.get_terminal_size()
        term_width = term_size.columns
        term_height = term_size.lines

        spacers_w = 3
        sidebar_w = self.SIDEBAR_WIDTH if self.show_sidebar else 0
        available_width = term_width - sidebar_w - spacers_w
        quad_width = max(10, available_width // 2)

        vertical_fixed = 5
        available_height = term_height - vertical_fixed
        quad_height = max(5, available_height // 2)

        return quad_width, quad_height

    def get_content(self):
        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        secondary_hex = colors["secondary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")

        term_width = shutil.get_terminal_size().columns
        console_width = max(10, term_width - 2)

        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, width=console_width)

        if self.active_tab == 0:  # Processes
            table = Table(
                show_header=True,
                header_style=f"bold {primary_hex}",
                box=None,
                expand=True,
            )
            table.add_column("PID", width=8, style="dim", no_wrap=True)
            table.add_column("Name", style="white", ratio=1)
            table.add_column("Threads", justify="right", style=secondary_hex, width=8)
            table.add_column("Handles", justify="right", style=secondary_hex, width=8)
            table.add_column("CPU%", justify="right", style=secondary_hex, width=8)
            table.add_column("MEM%", justify="right", style=secondary_hex, width=8)

            current_processes = list(self.processes)
            visible_rows = 20
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
                    table.add_row(
                        str(p["pid"]),
                        p["name"],
                        str(p.get("num_threads", 0)),
                        str(p.get("num_handles", 0)),
                        f"{p['cpu_percent']:.1f}",
                        f"{p['memory_percent']:.1f}",
                        style=style,
                    )
                except (IndexError, KeyError):
                    pass
            console.print(table)

        elif self.active_tab == 2:  # Startup
            table = Table(
                show_header=True,
                header_style=f"bold {primary_hex}",
                box=None,
                expand=True,
            )
            table.add_column("App Name", style="white", ratio=1)
            table.add_column("Status", justify="right", width=15)

            for i, (name, info) in enumerate(self.startup_apps):
                style = f"on {suggestion_bg}" if i == self.selected_index else ""
                status = "[green]Enabled[/]" if info["enabled"] else "[red]Disabled[/]"
                table.add_row(name, status, style=style)
            console.print(table)

        return ANSI(buffer.getvalue())

    def get_cpu(self):
        return ANSI(self.cpu_monitor.get_cached_frame())

    def get_ram(self):
        return ANSI(self.ram_monitor.get_cached_frame())

    def get_gpu(self):
        return ANSI(self.gpu_monitor.get_cached_frame())

    def get_network(self):
        return ANSI(self.net_monitor.get_cached_frame())

    def get_tabs_control(self):
        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        tabs = ["Processes", "Performance", "Startup"]
        text = []
        for i, tab in enumerate(tabs):
            is_focused = (
                self.app.layout.has_focus(self.tabs_window)
                if self.tabs_window
                else False
            )

            if i == self.active_tab:
                if is_focused:
                    text.append(("bg:#ffff00 fg:#000000 bold", f" [{tab}] "))
                else:
                    text.append((f"bg:{primary_hex} fg:#000000 bold", f" [{tab}] "))
            else:
                text.append(("class:tab", f" {tab} "))
            text.append(("", "   "))
        return text

    def get_hints(self):
        is_focused = (
            self.app.layout.has_focus(self.tabs_window) if self.tabs_window else False
        )
        if is_focused:
            return [
                (
                    "class:footer-pad",
                    " Left/Right: Switch Tab | Tab: Return to Content ",
                )
            ]
        else:
            return [
                ("class:footer-pad", " q: Quit | Tab: Focus Tabs | Arrows: Navigate ")
            ]

    def get_status_bar(self):
        return [("class:status", f" {os.getcwd()} | {socket.gethostname()} | v0.0.1 ")]
