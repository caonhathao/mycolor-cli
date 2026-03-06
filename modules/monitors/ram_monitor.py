import psutil

from .base_monitor import BaseMonitor


class RAMMonitor(BaseMonitor):
    def __init__(self):
        super().__init__(title="RAM Usage", color=None)

    def _do_update(self):
        try:
            val = psutil.virtual_memory().percent
            self.last_value = val
            self.history.append(val)
            if len(self.history) > 200:
                self.history.pop(0)
        except psutil.Error:
            pass