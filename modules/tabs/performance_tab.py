import io
import os
import shutil
import threading
import time
from time import monotonic
from .base_tab import BaseTab
from modules.monitors.cpu_monitor import CPUMonitor
from modules.monitors.gpu_monitor import GPUMonitor
from modules.monitors.net_monitor import NetMonitor
from modules.monitors.ram_monitor import RAMMonitor


def _log_debug(module_name, message):
    try:
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "crash_debug.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.time():.3f}] {module_name}: {message}\n")
    except Exception:
        pass


class PerformanceTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.cpu_monitor = CPUMonitor()
        self.ram_monitor = RAMMonitor()
        self.gpu_monitor = GPUMonitor()
        self.net_monitor = NetMonitor()
        self._data_changed = True
        
        self._worker_threads = []
        self._stop_event = threading.Event()
        self._last_invalidate_time = 0.0
        self._invalidate_lock = threading.Lock()

    def _try_invalidate(self):
        current_time = monotonic()
        if current_time - self._last_invalidate_time >= 0.1:
            with self._invalidate_lock:
                if current_time - self._last_invalidate_time >= 0.1:
                    self._last_invalidate_time = current_time
                    if self.parent.app.app_state.get("current_screen") == "taskmgr":
                        if self.parent.active_tab == self.parent.TAB_PERFORMANCE:
                            self.parent.app.invalidate()

    def start_workers(self, interval):
        if self._worker_threads:
            return
        
        def worker_cpu_ram():
            while not self._stop_event.is_set():
                try:
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER START:cpu_ram\n")
                    width, height = self._calculate_graph_dimensions()
                    if self.cpu_monitor.update():
                        with self.cpu_monitor._data_lock:
                            self.cpu_monitor.render(width, height)
                    if self.ram_monitor.update():
                        with self.ram_monitor._data_lock:
                            self.ram_monitor.render(width, height)
                    self._try_invalidate()
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER END:cpu_ram\n")
                except Exception:
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER ERROR:cpu_ram\n")
                self._stop_event.wait(interval)
        
        def worker_gpu():
            while not self._stop_event.is_set():
                try:
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER START:gpu\n")
                    width, height = self._calculate_graph_dimensions()
                    if self.gpu_monitor.update():
                        with self.gpu_monitor._data_lock:
                            self.gpu_monitor.render(width, height)
                    self._try_invalidate()
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER END:gpu\n")
                except Exception:
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER ERROR:gpu\n")
                self._stop_event.wait(interval * 2)
        
        def worker_net():
            while not self._stop_event.is_set():
                try:
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER START:net\n")
                    width, height = self._calculate_graph_dimensions()
                    if self.net_monitor.update():
                        with self.net_monitor._data_lock:
                            self.net_monitor.render(width, height)
                    self._try_invalidate()
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER END:net\n")
                except Exception:
                    with open("worker.log", "a") as f:
                        f.write(f"[{monotonic():.3f}] WORKER ERROR:net\n")
                self._stop_event.wait(interval)
        
        t1 = threading.Thread(target=worker_cpu_ram, daemon=True)
        t2 = threading.Thread(target=worker_gpu, daemon=True)
        t3 = threading.Thread(target=worker_net, daemon=True)
        
        self._worker_threads = [t1, t2, t3]
        for t in self._worker_threads:
            t.start()
        _log_debug("PERF", "workers_started")

    def stop_workers(self):
        self._stop_event.set()
        self._worker_threads = []
        _log_debug("PERF", "workers_stopped")

    def update(self, current_time: float) -> bool:
        return False

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
                    _log_debug("PERF", f"history_{m.title}: len={len(m.history)}, last={m.last_value}")
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
            skeleton = f"\x1b[90m{'═' * (width - 4)}\x1b[0m\n" * (height - 2)
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
        pass

    def on_deactivate(self):
        self.stop_workers()
        self.cpu_monitor.clear_data()
        self.ram_monitor.clear_data()
        self.gpu_monitor.clear_data()
        self.net_monitor.clear_data()