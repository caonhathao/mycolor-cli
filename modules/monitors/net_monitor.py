import io
from time import time

from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel

from .base_monitor import BaseMonitor


class DynamicSpeedScaler:
    BASELINE_BYTES = 1024 * 1024  # 1 MB/s baseline
    SCALE_INCREMENTS = [
        1024 * 1024,          # 1 MB/s
        2 * 1024 * 1024,     # 2 MB/s
        5 * 1024 * 1024,     # 5 MB/s
        10 * 1024 * 1024,    # 10 MB/s
        20 * 1024 * 1024,    # 20 MB/s
        50 * 1024 * 1024,    # 50 MB/s
        100 * 1024 * 1024,   # 100 MB/s
        200 * 1024 * 1024,   # 200 MB/s
        500 * 1024 * 1024,   # 500 MB/s
        1024 * 1024 * 1024,  # 1 GB/s
    ]
    THRESHOLD_RATIO = 0.4  # 40% of max
    COOLDOWN_SECONDS = 30
    DECAY_RATE = 0.95  # Gradual decay multiplier

    def __init__(self):
        self.current_max = self.BASELINE_BYTES
        self.baseline = self.BASELINE_BYTES
        self._last_below_threshold_time = None
        self._last_max_speed = self.current_max

    def update(self, current_speed: float) -> bool:
        scale_changed = False

        if current_speed > self.current_max:
            self._bump_ceiling(current_speed)
            self._last_below_threshold_time = None
            scale_changed = True
        elif current_speed < self.current_max * self.THRESHOLD_RATIO:
            if self._last_below_threshold_time is None:
                self._last_below_threshold_time = time()
            elif time() - self._last_below_threshold_time > self.COOLDOWN_SECONDS:
                if self._decay_ceiling():
                    scale_changed = True
        else:
            self._last_below_threshold_time = None

        if self.current_max != self._last_max_speed:
            scale_changed = True
            self._last_max_speed = self.current_max

        return scale_changed

    def _bump_ceiling(self, current_speed: float):
        for increment in self.SCALE_INCREMENTS:
            if increment > self.current_max and current_speed >= increment * 0.8:
                self.current_max = increment
                return
        for increment in self.SCALE_INCREMENTS:
            if increment > current_speed:
                self.current_max = increment
                return
        self.current_max = self.SCALE_INCREMENTS[-1]

    def _decay_ceiling(self) -> bool:
        if self.current_max > self.baseline:
            new_max = self.current_max * self.DECAY_RATE
            if new_max < self.baseline:
                self.current_max = self.baseline
                return True
            self.current_max = new_max
            return True
        return False


class NetMonitor(BaseMonitor):
    def __init__(self):
        import psutil
        super().__init__(title="Network", color=None)
        self.last_io = psutil.net_io_counters()
        self.last_time = time()
        self.scaler = DynamicSpeedScaler()
        self.down_history = [0.0] * 100
        self.up_history = [0.0] * 100
        self.last_down = 0.0
        self.last_up = 0.0
        self._data_changed = True

        self._buffer = io.StringIO()
        self._console = Console(file=self._buffer, force_terminal=True, width=80)

    def clear_data(self):
        super().clear_data()
        self.down_history = [0.0] * 100
        self.up_history = [0.0] * 100
        self.last_down = 0.0
        self.last_up = 0.0

    def _do_update(self):
        import psutil
        try:
            current_io = psutil.net_io_counters()
            current_time = time()

            elapsed = current_time - self.last_time
            if elapsed > 0:
                sent = current_io.bytes_sent - self.last_io.bytes_sent
                recv = current_io.bytes_recv - self.last_io.bytes_recv

                down_speed = recv / elapsed
                up_speed = sent / elapsed

                self.last_down = down_speed
                self.last_up = up_speed

                max_current = max(down_speed, up_speed)
                scale_changed = self.scaler.update(max_current)

                current_max = self.scaler.current_max

                down_percent = min(100.0, (down_speed / current_max) * 100.0)
                up_percent = min(100.0, (up_speed / current_max) * 100.0)

                self.down_history.append(down_percent)
                self.up_history.append(up_percent)

                if len(self.down_history) > 200:
                    self.down_history.pop(0)
                    self.up_history.pop(0)

                if scale_changed:
                    self._data_changed = True

            self.last_io = current_io
            self.last_time = current_time
        except psutil.Error:
            pass

    def _format_speed_fixed(self, bytes_per_sec):
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:7.1f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:7.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):7.1f} MB/s"

    def _format_speed(self, bytes_per_sec):
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.1f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    def _get_ceiling_label(self):
        return self._format_speed(self.scaler.current_max)

    def render(self, width, height, color=None, border_color=None, unit=""):
        if color is None:
            color = self.color
        if border_color is None:
            border_color = self.color

        ceiling_label = self._get_ceiling_label()

        h1 = height // 2
        h2 = height - h1

        inner_w = max(1, width - 4)
        inner_h1 = max(1, h1 - 2)
        graph_down = self._get_graph_text(self.down_history, inner_w, inner_h1, color)
        panel_down = Panel(
            Align.center(graph_down),
            title=f"[{color}]Download: {self._format_speed(self.last_down)}[/]",
            subtitle=f"[{border_color}]Max: {ceiling_label}[/]",
            border_style=border_color,
            width=width,
            height=h1,
            padding=(0, 1),
        )

        inner_h2 = max(1, h2 - 2)
        graph_up = self._get_graph_text(self.up_history, inner_w, inner_h2, color)
        panel_up = Panel(
            Align.center(graph_up),
            title=f"[{color}]Upload: {self._format_speed(self.last_up)}[/]",
            subtitle=f"[{border_color}]Max: {ceiling_label}[/]",
            border_style=border_color,
            width=width,
            height=h2,
            padding=(0, 1),
        )

        self._buffer.seek(0)
        self._buffer.truncate(0)
        self._console.width = width
        self._console.print(Group(panel_down, panel_up))
        self.cached_frame = self._buffer.getvalue()
