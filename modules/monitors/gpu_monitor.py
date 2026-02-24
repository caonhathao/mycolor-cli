from .base_monitor import BaseMonitor
try:
    import GPUtil
except ImportError:
    GPUtil = None

class GPUMonitor(BaseMonitor):
    def __init__(self):
        super().__init__(title="GPU Usage", color="magenta")

    def update(self):
        val = 0.0
        if GPUtil:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    val = gpus[0].load * 100.0
            except Exception:
                pass
        
        self.last_value = val
        self.history.append(val)
        if len(self.history) > 200:
            self.history.pop(0)