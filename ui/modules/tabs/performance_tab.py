import io
import os
import shutil
import threading
import time
import traceback
from time import monotonic
from .base_tab import BaseTab
from services.monitors.cpu_monitor import CPUMonitor
from services.monitors.gpu_monitor import GPUMonitor
from services.monitors.net_monitor import NetMonitor
from services.monitors.ram_monitor import RAMMonitor
from core.logger import get_worker_logger

REFRESH_INTERVAL = 0.5

_worker_logger = get_worker_logger()


def _log_lifecycle(thread_name, message):
    _worker_logger.log_lifecycle(thread_name, f"{thread_name}: {message}")


def _log_render(message):
    _worker_logger.log_render(message)


def _log_debug(module_name, message):
    _worker_logger.log_ui_access(f"{module_name}: {message}")


class PerformanceTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.cpu_monitor = CPUMonitor()
        self.ram_monitor = RAMMonitor()
        self.gpu_monitor = GPUMonitor()
        self.net_monitor = NetMonitor()
        self._data_changed = True

        self._worker_threads = []
        self._stop_event_cpu_ram = threading.Event()
        self._stop_event_gpu = threading.Event()
        self._stop_event_net = threading.Event()
        self._last_invalidate_time = 0.0
        self._invalidate_lock = threading.Lock()
        self._monitors = [self.cpu_monitor, self.ram_monitor, self.gpu_monitor, self.net_monitor]
        self._has_update = False

    def _try_invalidate(self):
        try:
            screen = self.parent.app.app_state.get("current_screen", "unknown")
            tab = self.parent.active_tab
        except Exception:
            return
        
        current_time = monotonic()
        if current_time - self._last_invalidate_time >= 0.1:
            with self._invalidate_lock:
                if current_time - self._last_invalidate_time >= 0.1:
                    self._last_invalidate_time = current_time
                    app_id = id(self.parent.app)
                    _log_render(f"RENDER_CHECK: _has_update={self._has_update}, app_id={app_id}, screen={screen}, tab={tab}")
                    if screen == "taskmgr" and tab == self.parent.TAB_PERFORMANCE:
                        self._has_update = True
                        _log_debug("PERF", f"INVALIDATE_SIGNAL: tab={tab}, screen={screen}, app_id={app_id}")
                        try:
                            app = self.parent.app.app_state.get("app_instance")
                            if app:
                                app_id_from_state = id(app)
                                _log_render(f"INVALIDATE: signaling App {app_id_from_state} (matches parent.app={app_id_from_state == app_id})")
                                app.invalidate()
                            else:
                                _log_render("INVALIDATE_FAIL: app_instance is None")
                        except Exception as e:
                            _log_render(f"INVALIDATE_ERROR: {e}")
                    else:
                        _log_debug("PERF", f"INVALIDATE_SKIP: tab={tab}, screen={screen}")
        
        with self._invalidate_lock:
            if screen == "taskmgr" and tab == self.parent.TAB_PERFORMANCE:
                try:
                    app = self.parent.app.app_state.get("app_instance")
                    if app:
                        app.invalidate()
                except Exception:
                    pass

    def start_workers(self, interval):
        if self._worker_threads:
            return

        _log_debug("PERF", "start_workers CALLED")
        _log_debug("PERF", f"PRE-START events: cpu={self._stop_event_cpu_ram.is_set()}, gpu={self._stop_event_gpu.is_set()}, net={self._stop_event_net.is_set()}")

        self._stop_event_cpu_ram.clear()
        self._stop_event_gpu.clear()
        self._stop_event_net.clear()

        _log_debug("PERF", "POST-CLEAR events: all FALSE")

        def worker_cpu_ram():
            _log_lifecycle("CPU_RAM", f"THREAD STARTED | cpu_id={id(self.cpu_monitor)} ram_id={id(self.ram_monitor)}")
            while not self._stop_event_cpu_ram.is_set():
                _log_lifecycle("CPU_RAM", f"PULSE: event_set={self._stop_event_cpu_ram.is_set()}")
                try:
                    width, height = self._calculate_graph_dimensions()
                    if self.cpu_monitor.update():
                        cpu_val = self.cpu_monitor.last_value
                        _log_lifecycle("CPU_RAM", f"FETCHED: CPU={cpu_val} | hist_len={len(self.cpu_monitor.history)}")
                        with self.cpu_monitor._data_lock:
                            self.cpu_monitor.render(width, height)
                    if self.ram_monitor.update():
                        ram_val = self.ram_monitor.last_value
                        _log_lifecycle("CPU_RAM", f"FETCHED: RAM={ram_val} | hist_len={len(self.ram_monitor.history)}")
                        with self.ram_monitor._data_lock:
                            self.ram_monitor.render(width, height)
                    self._try_invalidate()
                except Exception:
                    _worker_logger.log_error("worker_cpu_ram", traceback.format_exc())
                self._stop_event_cpu_ram.wait(interval)
            _log_lifecycle("CPU_RAM", "THREAD EXITED (loop ended)")

        def worker_gpu():
            _log_lifecycle("GPU", "THREAD STARTED")
            while not self._stop_event_gpu.is_set():
                _log_lifecycle("GPU", f"PULSE: event_set={self._stop_event_gpu.is_set()}")
                try:
                    width, height = self._calculate_graph_dimensions()
                    if self.gpu_monitor.update():
                        with self.gpu_monitor._data_lock:
                            self.gpu_monitor.render(width, height)
                    self._try_invalidate()
                except Exception:
                    _worker_logger.log_error("worker_gpu", traceback.format_exc())
                self._stop_event_gpu.wait(interval * 2)
            _log_lifecycle("GPU", "THREAD EXITED (loop ended)")

        def worker_net():
            _log_lifecycle("NET", "THREAD STARTED")
            while not self._stop_event_net.is_set():
                _log_lifecycle("NET", f"PULSE: event_set={self._stop_event_net.is_set()}")
                try:
                    width, height = self._calculate_graph_dimensions()
                    if self.net_monitor.update():
                        with self.net_monitor._data_lock:
                            self.net_monitor.render(width, height)
                    self._try_invalidate()
                except Exception:
                    _worker_logger.log_error("worker_net", traceback.format_exc())
                self._stop_event_net.wait(interval)
            _log_lifecycle("NET", "THREAD EXITED (loop ended)")

        t1 = threading.Thread(target=worker_cpu_ram, daemon=True, name="CPU_RAM")
        t2 = threading.Thread(target=worker_gpu, daemon=True, name="GPU")
        t3 = threading.Thread(target=worker_net, daemon=True, name="NET")

        self._worker_threads = [t1, t2, t3]
        for t in self._worker_threads:
            t.start()

        _log_debug("PERF", "workers_started")

    def stop_workers(self):
        _log_debug("PERF", "STOP_REQUESTED")
        self._stop_event_cpu_ram.set()
        self._stop_event_gpu.set()
        self._stop_event_net.set()
        for t in self._worker_threads:
            t.join(timeout=1.0)
        self._worker_threads = []
        self._stop_event_cpu_ram.clear()
        self._stop_event_gpu.clear()
        self._stop_event_net.clear()
        _log_debug("PERF", "workers_stopped")

    def update(self, current_time: float) -> bool:
        if self._has_update:
            self._has_update = False
            return True
        return False

    def mark_dirty(self):
        self._has_update = True

    def _calculate_graph_dimensions(self):
        term_size = shutil.get_terminal_size()
        term_width = term_size.columns
        term_height = term_size.lines

        sidebar_w = self.parent.SIDEBAR_WIDTH if self.parent.show_sidebar else 0
        spacers_w = 3
        available_width = term_width - sidebar_w - spacers_w
        quad_width = max(10, available_width // 2)

        vertical_fixed = 5
        available_height = term_height - vertical_fixed
        quad_height = max(5, available_height // 2)

        return quad_width, quad_height

    def _has_data(self):
        for m in [self.cpu_monitor, self.ram_monitor, self.gpu_monitor, self.net_monitor]:
            try:
                with m._data_lock:
                    hist_len = len(m.history)
                    last_val = m.last_value
                    _log_debug("PERF", f"DATA: {m.title} history_len={hist_len}, last={last_val}")
            except Exception:
                _log_debug("PERF", f"lock_failed_{m.title}")

        for m in [self.cpu_monitor, self.ram_monitor, self.gpu_monitor, self.net_monitor]:
            try:
                with m._data_lock:
                    if m.last_value > 0 or len(m.history) > 1:
                        return True
            except Exception:
                pass
        return False

    def render(self):
        _log_debug("PERF", "render_start")
        width, height = self._calculate_graph_dimensions()

        if not self._has_data():
            _log_debug("PERF", "render_skeleton")
            skeleton = f"\x1b[90m{'=' * (width - 4)}\x1b[0m\n" * (height - 2)
            skeleton += f"\x1b[90m[\x1b[0m Collecting metrics... \x1b[90m]\x1b[0m"
            return {
                "cpu": skeleton,
                "ram": skeleton,
                "gpu": skeleton,
                "net": skeleton,
            }

        def safe_get(monitor):
            frame = ""
            if hasattr(monitor, 'get_cached_frame_safe'):
                frame = monitor.get_cached_frame_safe()
            else:
                frame = monitor.get_cached_frame()
            _log_debug("PERF", f"frame_len_{monitor.title}: {len(frame)}")
            return frame

        result = {
            "cpu": safe_get(self.cpu_monitor),
            "ram": safe_get(self.ram_monitor),
            "gpu": safe_get(self.gpu_monitor),
            "net": safe_get(self.net_monitor),
        }
        _log_debug("PERF", "render_done")
        return result

    def on_activate(self):
        _log_debug("PERF", f"on_activate CALLED: existing_threads={len(self._worker_threads)}")
        self._has_update = True
        if not self._worker_threads:
            self.start_workers(REFRESH_INTERVAL)
        else:
            _log_debug("PERF", "SKIP_start_workers: threads already running")

    def on_deactivate(self):
        _log_debug("PERF", "on_deactivate CALLED")
        self.stop_workers()