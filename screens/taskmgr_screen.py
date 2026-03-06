import asyncio
import os
import shutil
import socket
from time import time

from prompt_toolkit.formatted_text import ANSI

from functions.theme.theme_logic import get_current_theme_colors
from modules.panels.detail_panel import DetailPanel
from modules.tabs import ProcessesTab, PerformanceTab, StartupTab


class TaskManagerInterface:
    TAB_PROCESSES = 0
    TAB_PERFORMANCE = 1
    TAB_STARTUP = 2

    def __init__(self, app):
        self.app = app
        self.active_tab = 0
        self.focus_mode = "content"
        self.running = True
        self.last_term_size = (0, 0)
        self.first_render = True
        self.tabs_window = None

        self._data_changed = True

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

        self.tabs = {
            self.TAB_PROCESSES: ProcessesTab(self),
            self.TAB_PERFORMANCE: PerformanceTab(self),
            self.TAB_STARTUP: StartupTab(self),
        }

        self.detail_panel = DetailPanel()

        self.app.create_background_task(self.update_loop())

        self._data_changed = True

    def _load_initial_visibility(self):
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
                    current_tab = self.tabs[self.active_tab]

                    if current_tab.update(current_time):
                        self._data_changed = True

                    if self.show_sidebar:
                        self.detail_panel.update()
                        self._data_changed = True

                    if self._data_changed:
                        self.app.invalidate()
                        self._data_changed = False

                await asyncio.sleep(0.1)
        finally:
            if hasattr(self, "gpu_monitor"):
                if hasattr(self.tabs[self.TAB_PERFORMANCE].gpu_monitor, "stop"):
                    self.tabs[self.TAB_PERFORMANCE].gpu_monitor.stop()
            if hasattr(self, "detail_panel") and hasattr(self.detail_panel, "stop"):
                self.detail_panel.stop()

    def get_header(self):
        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        header_text = colors.get("header_text", "black")
        hostname = socket.gethostname()
        return [(f"bg:{primary_hex} fg:{header_text} bold", f" SYSTEM MONITOR - {hostname} ")]

    def get_sidebar(self):
        return self.detail_panel.render(self.SIDEBAR_WIDTH)

    def get_content(self):
        return self.tabs[self.active_tab].render()

    def get_cpu(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        return ANSI(perf_tab.cpu_monitor.get_cached_frame())

    def get_ram(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        return ANSI(perf_tab.ram_monitor.get_cached_frame())

    def get_gpu(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        return ANSI(perf_tab.gpu_monitor.get_cached_frame())

    def get_network(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        return ANSI(perf_tab.net_monitor.get_cached_frame())

    def get_tabs_control(self):
        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        tab_accent = colors.get("tab_accent", colors.get("active_tab", "#FFFF00"))
        inactive_tab_color = colors.get("inactive_tab", "#888888")
        header_text = colors.get("header_text", "white")
        tab_names = ["Processes", "Performance", "Startup"]
        text = []
        for i, tab in enumerate(tab_names):
            is_focused = (
                self.app.layout.has_focus(self.tabs_window)
                if self.tabs_window
                else False
            )

            if i == self.active_tab:
                bracket_style = f"fg:{tab_accent} bold"
                text.append((f"fg:{header_text}", f"["))
                text.append((bracket_style, f"{tab}"))
                text.append((f"fg:{header_text}", f"]"))
            else:
                text.append((f"class:tab fg:{inactive_tab_color}", f" {tab} "))
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
