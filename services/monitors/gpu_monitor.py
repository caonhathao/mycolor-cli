import platform
import threading
from time import sleep, time

from .base_monitor import BaseMonitor

try:
    import GPUtil
except ImportError:
    GPUtil = None

try:
    import pythoncom
    import wmi
except ImportError:
    wmi = None
    pythoncom = None


GPU_FAILURE_LIMIT = 3


class WindowsGPULoader(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.running = True
        self.latest_usage = 0.0
        self.paused = False
        self.start_time = time()

    def run(self):
        if not wmi or not pythoncom:
            return

        try:
            pythoncom.CoInitialize()
            w = wmi.WMI(namespace="root/CIMV2")
        except (wmi.x_wmi, pythoncom.com_error):
            self.running = False
            return

        while self.running:
            try:
                if self.paused:
                    sleep(0.5)
                    continue

                results = w.query(
                    "SELECT UtilizationPercentage FROM Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine WHERE Name LIKE '%3D' OR Name LIKE '%Video Decode'"
                )
                max_util = 0.0
                if results:
                    for item in results:
                        try:
                            u = float(item.UtilizationPercentage)
                            if u > max_util:
                                max_util = u
                        except (ValueError, TypeError, AttributeError):
                            continue
                self.latest_usage = max_util
            except (wmi.x_wmi, pythoncom.com_error):
                pass

            elapsed = time() - self.start_time
            sleep_duration = 1.0 if elapsed < 10 else 5.0

            chunks = int(sleep_duration / 0.1)
            for _ in range(chunks):
                if not self.running:
                    break
                if self.paused:
                    break
                sleep(0.1)

        try:
            pythoncom.CoUninitialize()
        except pythoncom.com_error:
            pass

    def stop(self):
        self.running = False


class GPUMonitor(BaseMonitor):
    def __init__(self):
        super().__init__(title="GPU Usage", color=None)
        self.use_wmi = False
        self.loader = None
        self._initialized = False
        self._failure_count = 0
        self._disabled = True  # Disabled by default - causes freezes

    def _do_update(self):
        # GPU monitoring disabled for stability
        self.last_value = 0.0
        self.history.append(0.0)
        if len(self.history) > 200:
            self.history.pop(0)

    def stop(self):
        if self.loader:
            self.loader.stop()

    def pause(self):
        if self.loader:
            self.loader.paused = True

    def resume(self):
        if self.loader:
            self.loader.paused = False