import asyncio
import os
import shutil
import socket
import threading
from datetime import datetime
from time import time, monotonic
import json as json_lib

from prompt_toolkit.formatted_text import ANSI

from functions.theme.theme_logic import _get_config_path
from modules.constants import get_theme_primary, get_theme_color, get_colors_dict, THEME_COLORS
from modules.panels.detail_panel import DetailPanel
from modules.tabs import ProcessesTab, PerformanceTab, StartupTab


def _get_logs_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

def _write_log(filename, message):
    try:
        logs_dir = _get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)
        with open(os.path.join(logs_dir, filename), "a") as f:
            f.write(message)
    except Exception:
        pass


def _load_taskmgr_config():
    try:
        from functions.theme.theme_logic import _get_config_path
        config_path = _get_config_path()
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json_lib.load(f)
    except Exception:
        pass
    return {"process_update_interval": 3.0, "taskmgr": {"process_limit": 20, "exclude_system_apps": True}}


_taskmgr_config = _load_taskmgr_config()
REFRESH_INTERVAL = _taskmgr_config.get("process_update_interval", 3.0)


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
        self._stop_event = threading.Event()
        self._data_lock = threading.Lock()
        self._first_pulse = True

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

        self._worker_thread = threading.Thread(target=self._background_worker, daemon=True)
        self._worker_thread.start()

        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        if hasattr(perf_tab, 'start_workers'):
            perf_tab.start_workers(REFRESH_INTERVAL)

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

    def _background_worker(self):
        import traceback
        from time import monotonic
        logs_dir = _get_logs_dir()
        os.makedirs(logs_dir, exist_ok=True)
        
        while not self._stop_event.is_set():
            try:
                if self.app.app_state.get("current_screen") == "taskmgr":
                    mode = "w" if self._first_pulse else "a"
                    with open(os.path.join(logs_dir, "pulse.log"), mode) as f:
                        if self._first_pulse:
                            f.write(f"=== SESSION STARTED: {datetime.now()} | PID: {os.getpid()} ===\n")
                            self._first_pulse = False
                        f.write(f"[{monotonic():.3f}] UI PULSE | tab:{self.active_tab} | screen:{self.app.app_state.get('current_screen')}\n")
                    current_time = time()
                    current_tab = self.tabs[self.active_tab]
                    
                    if current_tab.update(current_time):
                        with self._data_lock:
                            self._data_changed = True

                        if self.show_sidebar and self.active_tab != self.TAB_PERFORMANCE:
                            if self.detail_panel.update():
                                with self._data_lock:
                                    self._data_changed = True
            except Exception:
                try:
                    with open(os.path.join(logs_dir, "error_runtime.log"), "a") as f:
                        f.write(f"[{monotonic():.3f}] _background_worker ERROR:\n")
                        f.write(traceback.format_exc())
                except Exception:
                    pass

            self._stop_event.wait(REFRESH_INTERVAL)

        try:
            perf_tab = self.tabs[self.TAB_PERFORMANCE]
            if hasattr(perf_tab, 'stop_workers'):
                perf_tab.stop_workers()
        except Exception:
            pass
        try:
            if hasattr(self, "detail_panel") and hasattr(self.detail_panel, "stop"):
                self.detail_panel.stop()
        except Exception:
            pass

    def switch_tab(self, direction):
        old_tab = self.tabs[self.active_tab]
        old_tab.on_deactivate()
        self.active_tab = (self.active_tab + direction) % 3
        new_tab = self.tabs[self.active_tab]
        new_tab.selected_index = 0
        new_tab.scroll_offset = 0
        new_tab.on_activate()
        
        if hasattr(new_tab, 'start_workers'):
            new_tab.start_workers(REFRESH_INTERVAL)
        
        with self._data_lock:
            self._data_changed = True
            if hasattr(new_tab, 'last_fetch_time'):
                new_tab.last_fetch_time = 0
        
        self.app.renderer.clear()
        self.app.invalidate()

    def stop(self):
        self._stop_event.set()
        self.running = False

    async def update_loop(self):
        try:
            while self.running:
                current_width = shutil.get_terminal_size().columns
                new_mode = "full" if current_width >= self.FULL_THRESHOLD else "mini"

                if new_mode != self.current_mode:
                    self._apply_blueprint(new_mode)
                    self.show_sidebar = new_mode == "full"
                    self.app.renderer.erase()
                    self.app.invalidate()

                current_term_size = shutil.get_terminal_size()
                if current_term_size != self.last_term_size or self.first_render:
                    self.last_term_size = current_term_size
                    self.first_render = False
                    self.app.renderer.clear()
                    self.app.invalidate()

                if self.app.app_state.get("current_screen") == "taskmgr":
                    self.app.invalidate()
                    with self._data_lock:
                        self._data_changed = False

                _write_log("pulse.log", f"[{monotonic():.3f}] UI PULSE | tab:{self.active_tab} | screen:{self.app.app_state.get('current_screen')}\n")

                await asyncio.sleep(0.1)
        finally:
            self._stop_event.set()

    def get_header(self):
        primary_hex = get_theme_primary()
        header_text = get_theme_color("header_text", THEME_COLORS["header_text"])
        hostname = socket.gethostname()
        return [(f"bg:{primary_hex} fg:{header_text} bold", f" SYSTEM MONITOR - {hostname} ")]

    def get_sidebar(self):
        return self.detail_panel.render(self.SIDEBAR_WIDTH)

    def get_content(self):
        return self.tabs[self.active_tab].render()

    def get_cpu(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        _write_log("ui_data_access.log", f"[{monotonic():.3f}] get_cpu() | monitor_id={id(perf_tab.cpu_monitor)} | last={perf_tab.cpu_monitor.last_value} | hist_len={len(perf_tab.cpu_monitor.history)}\n")
        formatted = perf_tab.cpu_monitor.get_cached_formatted()
        if formatted:
            return formatted
        return ANSI(perf_tab.cpu_monitor.get_cached_frame_safe())

    def get_ram(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        _write_log("ui_data_access.log", f"[{monotonic():.3f}] get_ram() | monitor_id={id(perf_tab.ram_monitor)} | last={perf_tab.ram_monitor.last_value} | hist_len={len(perf_tab.ram_monitor.history)}\n")
        formatted = perf_tab.ram_monitor.get_cached_formatted()
        if formatted:
            return formatted
        return ANSI(perf_tab.ram_monitor.get_cached_frame_safe())

    def get_gpu(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        _write_log("ui_data_access.log", f"[{monotonic():.3f}] get_gpu() | monitor_id={id(perf_tab.gpu_monitor)} | last={perf_tab.gpu_monitor.last_value} | hist_len={len(perf_tab.gpu_monitor.history)}\n")
        formatted = perf_tab.gpu_monitor.get_cached_formatted()
        if formatted:
            return formatted
        return ANSI(perf_tab.gpu_monitor.get_cached_frame_safe())

    def get_network(self):
        perf_tab = self.tabs[self.TAB_PERFORMANCE]
        _write_log("ui_data_access.log", f"[{monotonic():.3f}] get_net() | monitor_id={id(perf_tab.net_monitor)} | last={perf_tab.net_monitor.last_value} | hist_len={len(perf_tab.net_monitor.history)}\n")
        formatted = perf_tab.net_monitor.get_cached_formatted()
        if formatted:
            return formatted
        return ANSI(perf_tab.net_monitor.get_cached_frame_safe())

    def get_tabs_control(self):
        colors = get_colors_dict()
        primary_hex = get_theme_primary()
        tab_accent = get_theme_color("tab_accent", THEME_COLORS.get("accent", "#FFFF00"))
        inactive_tab_color = get_theme_color("inactive_tab", "#888888")
        header_text = get_theme_color("header_text", THEME_COLORS["header_text"])
        tab_names = ["Processes", "Performance", "Startup"]
        text = []
        for i, tab in enumerate(tab_names):
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
        return [
            ("class:footer-pad", " q: Quit | ←→: Switch Tabs ")
        ]

    def get_status_bar(self):
        return [("class:status", f" {os.getcwd()} | {socket.gethostname()} | v0.0.1 ")]