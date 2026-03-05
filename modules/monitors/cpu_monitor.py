import psutil

from .base_monitor import BaseMonitor


class CPUMonitor(BaseMonitor):
    def __init__(self):
        super().__init__(title="CPU Usage", color="green")
        # Initialize cpu_percent to start measurement
        psutil.cpu_percent(interval=None)

    def update(self):
        if not self.should_update():
            return
        try:
            val = psutil.cpu_percent(interval=None)
            self.last_value = val
            self.history.append(val)
            if len(self.history) > 200:
                self.history.pop(0)
        except psutil.Error:
            pass