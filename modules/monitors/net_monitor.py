import psutil
import time
import io
from rich.console import Console, Group
from rich.panel import Panel
from rich.align import Align
from .base_monitor import BaseMonitor

class NetMonitor(BaseMonitor):
    def __init__(self):
        super().__init__(title="Network", color="blue")
        self.last_io = psutil.net_io_counters()
        self.last_time = time.time()
        self.max_speed = 1024 * 1024 # 1MB/s baseline
        self.down_history = [0.0] * 100
        self.up_history = [0.0] * 100
        self.last_down = 0.0
        self.last_up = 0.0

    def update(self):
        try:
            current_io = psutil.net_io_counters()
            current_time = time.time()
            
            elapsed = current_time - self.last_time
            if elapsed > 0:
                sent = current_io.bytes_sent - self.last_io.bytes_sent
                recv = current_io.bytes_recv - self.last_io.bytes_recv
                
                down_speed = recv / elapsed
                up_speed = sent / elapsed
                
                self.last_down = down_speed
                self.last_up = up_speed
                
                # Auto-scale max speed
                current_max = max(down_speed, up_speed)
                if current_max > self.max_speed:
                    self.max_speed = current_max
                elif self.max_speed > 1024 * 1024:
                    self.max_speed *= 0.99
                
                down_percent = min(100.0, (down_speed / self.max_speed) * 100.0)
                up_percent = min(100.0, (up_speed / self.max_speed) * 100.0)
                
                self.down_history.append(down_percent)
                self.up_history.append(up_percent)
                
                if len(self.down_history) > 200:
                    self.down_history.pop(0)
                    self.up_history.pop(0)
            
            self.last_io = current_io
            self.last_time = current_time
        except Exception:
            pass

    def _format_speed(self, bytes_per_sec):
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    def render(self, width, height, color=None, border_color=None, unit=""):
        if color is None: color = self.color
        if border_color is None: border_color = self.color
        
        h1 = height // 2
        h2 = height - h1
        
        # Down Panel
        inner_w = max(1, width - 4)
        inner_h1 = max(1, h1 - 2)
        graph_down = self._get_graph_text(self.down_history, inner_w, inner_h1, color)
        panel_down = Panel(Align.center(graph_down), title=f"[{color}]Download: {self._format_speed(self.last_down)}[/]", border_style=border_color, width=width, height=h1, padding=(0,1))
        
        # Up Panel
        inner_h2 = max(1, h2 - 2)
        graph_up = self._get_graph_text(self.up_history, inner_w, inner_h2, color)
        panel_up = Panel(Align.center(graph_up), title=f"[{color}]Upload: {self._format_speed(self.last_up)}[/]", border_style=border_color, width=width, height=h2, padding=(0,1))
        
        console = Console(file=io.StringIO(), force_terminal=True, width=width)
        console.print(Group(panel_down, panel_up))
        self.cached_frame = console.file.getvalue()