import psutil
import time
from .base_monitor import BaseMonitor
from rich.console import Group, Console
import io

class NetMonitor:
    def __init__(self):
        self.down_monitor = BaseMonitor("Download Speed")
        self.up_monitor = BaseMonitor("Upload Speed")
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()
        self.cached_frame = ""

    def poll(self):
        curr_io = psutil.net_io_counters()
        curr_time = time.time()
        
        delta = curr_time - self.last_time
        if delta <= 0: delta = 0.5
        
        recv = (curr_io.bytes_recv - self.last_io.bytes_recv) / delta
        sent = (curr_io.bytes_sent - self.last_io.bytes_sent) / delta
        
        self.down_monitor.update_data(recv)
        self.up_monitor.update_data(sent)
        
        self.last_io = curr_io
        self.last_time = curr_time

    def render(self, width, height, primary_hex, secondary_hex):
        group = self.render_graph(width, height, primary_hex, secondary_hex)
        console = Console(file=io.StringIO(), force_terminal=True, width=width)
        console.print(group)
        self.cached_frame = console.file.getvalue()

    def get_cached_frame(self):
        return self.cached_frame

    def render_graph(self, width, height, primary_hex, secondary_hex):
        h = height // 2
        def fmt(val):
            if val < 1024: return f"{val:.0f} B/s"
            if val < 1024**2: return f"{val/1024:.1f} KB/s"
            return f"{val/1024**2:.1f} MB/s"
            
        return Group(
            self.down_monitor.render_graph(width, h, primary_hex, secondary_hex, value_color="red", auto_scale=True, formatter=fmt),
            self.up_monitor.render_graph(width, h, primary_hex, secondary_hex, value_color="red", auto_scale=True, formatter=fmt)
        )