import shutil
from .base_tab import BaseTab
from modules.monitors.cpu_monitor import CPUMonitor
from modules.monitors.gpu_monitor import GPUMonitor
from modules.monitors.net_monitor import NetMonitor
from modules.monitors.ram_monitor import RAMMonitor


class PerformanceTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.cpu_monitor = CPUMonitor()
        self.ram_monitor = RAMMonitor()
        self.gpu_monitor = GPUMonitor()
        self.net_monitor = NetMonitor()
        self._data_changed = True

    def update(self, current_time: float) -> bool:
        if hasattr(self.gpu_monitor, "resume"):
            self.gpu_monitor.resume()

        width, height = self._calculate_graph_dimensions()
        any_updated = False

        if self.cpu_monitor.update():
            self.cpu_monitor.render(width, height)
            self._data_changed = True
            any_updated = True
        if self.ram_monitor.update():
            self.ram_monitor.render(width, height)
            self._data_changed = True
            any_updated = True
        if self.gpu_monitor.update():
            self.gpu_monitor.render(width, height)
            self._data_changed = True
            any_updated = True
        if self.net_monitor.update():
            self.net_monitor.render(width, height)
            self._data_changed = True
            any_updated = True

        return any_updated

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

    def render(self):
        width, height = self._calculate_graph_dimensions()
        return {
            "cpu": self.cpu_monitor.get_cached_frame(),
            "ram": self.ram_monitor.get_cached_frame(),
            "gpu": self.gpu_monitor.get_cached_frame(),
            "net": self.net_monitor.get_cached_frame(),
        }

    def on_activate(self):
        if hasattr(self.gpu_monitor, "resume"):
            self.gpu_monitor.resume()

    def on_deactivate(self):
        if hasattr(self.gpu_monitor, "pause"):
            self.gpu_monitor.pause()
