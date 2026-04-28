from services.monitors.cpu_monitor import CPUMonitor
from services.monitors.ram_monitor import RAMMonitor
from services.monitors.gpu_monitor import GPUMonitor
from services.monitors.net_monitor import NetMonitor


class SystemDataBridge:
    def __init__(self):
        self._cpu = None
        self._ram = None
        self._gpu = None
        self._net = None

    def get_cpu_monitor(self):
        if self._cpu is None:
            self._cpu = CPUMonitor()
        return self._cpu

    def get_ram_monitor(self):
        if self._ram is None:
            self._ram = RAMMonitor()
        return self._ram

    def get_gpu_monitor(self):
        if self._gpu is None:
            self._gpu = GPUMonitor()
        return self._gpu

    def get_net_monitor(self):
        if self._net is None:
            self._net = NetMonitor()
        return self._net

    def get_all_monitors(self):
        return {
            "cpu": self.get_cpu_monitor(),
            "ram": self.get_ram_monitor(),
            "gpu": self.get_gpu_monitor(),
            "net": self.get_net_monitor(),
        }

    def start_monitoring(self, monitor_types=None):
        if monitor_types is None:
            monitor_types = ["cpu", "ram", "gpu", "net"]

        monitors = self.get_all_monitors()
        for monitor_type in monitor_types:
            monitor = monitors.get(monitor_type)
            if monitor:
                monitor.update()

    def clear_all(self):
        monitors = self.get_all_monitors()
        for monitor in monitors.values():
            if monitor:
                monitor.clear_data()


_bridge = None


def get_system_bridge():
    global _bridge
    if _bridge is None:
        _bridge = SystemDataBridge()
    return _bridge