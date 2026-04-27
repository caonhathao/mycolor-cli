import io
import os
import json
import threading
from time import monotonic

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from commands.functions.theme.theme_logic import get_current_theme_colors
from prompt_toolkit.formatted_text import ANSI as PT_ANSI


def _load_interval():
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(base_dir, "config", "settings.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f).get("process_update_interval", 0.5)
    except Exception:
        pass
    return 0.5


_MONITOR_INTERVAL = _load_interval()


class BaseMonitor:
    def __init__(self, title="Monitor", color=None):
        self.title = title
        colors = get_current_theme_colors()
        self.color = color if color else colors.get("monitor_graph", "green")
        self.history = []
        self.last_value = 0.0
        self.cached_frame = ""
        self._cached_formatted = None
        self.blocks = [" ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

        self.update_interval = 0.5
        self.last_update_time = 0.0

        self._buffer = io.StringIO()
        self._console = Console(file=self._buffer, force_terminal=True, width=80)

        self._data_lock = threading.Lock()

    def get_cached_frame_safe(self):
        with self._data_lock:
            result = self.cached_frame
        return result

    def should_update(self):
        """Check if enough time has passed to perform an update."""
        # First render: update immediately without waiting
        if self.last_update_time == 0:
            return True
        
        current_time = monotonic()
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            return True
        return False

    def update(self):
        """Update monitor data. Returns True if data was refreshed, False otherwise."""
        if self.should_update():
            self._do_update()
            return True
        return False

    def _do_update(self):
        pass

    def set_error_state(self):
        self.last_value = 0.0

    def get_cached_frame(self):
        return self.cached_frame

    def get_cached_formatted(self):
        with self._data_lock:
            self._cached_formatted = PT_ANSI(self.cached_frame)
        return self._cached_formatted

    def clear_data(self):
        """Clear monitor data to free memory when tab is inactive."""
        self.history = [0.0] * 100
        self.cached_frame = ""
        self._cached_formatted = None
        self.last_value = 0.0
        self.last_update_time = 0.0

    def _get_graph_text(self, data, width, height, color):
        data_slice = data[-width:]
        if len(data_slice) < width:
            data_slice = [0.0] * (width - len(data_slice)) + data_slice

        graph_rows = [[" " for _ in range(width)] for _ in range(height)]

        for x, val in enumerate(data_slice):
            # Normalize value (0-100) to height
            h = (val / 100.0) * height
            full_blocks = int(h)
            remainder = h - full_blocks

            # Fill full blocks from bottom
            for y in range(full_blocks):
                row_idx = height - 1 - y
                if 0 <= row_idx < height:
                    graph_rows[row_idx][x] = "█"

            # Add partial block
            if remainder > 0 and full_blocks < height:
                idx = int(remainder * 8)
                if idx > 7:
                    idx = 7
                row_idx = height - 1 - full_blocks
                if 0 <= row_idx < height:
                    graph_rows[row_idx][x] = self.blocks[idx]

        graph_text = Text()
        for row in graph_rows:
            graph_text.append("".join(row) + "\n", style=color)
        return graph_text

    def render(self, width, height, color=None, border_color=None, unit="%"):
        if color is None:
            color = self.color
        if border_color is None:
            border_color = self.color

        # Calculate inner dimensions (accounting for border and padding)
        inner_width = max(1, width - 4)
        inner_height = max(1, height - 2)

        graph_text = self._get_graph_text(
            self.history, inner_width, inner_height, color
        )

        panel = Panel(
            Align.center(graph_text),
            title=f"[{color}]{self.title}: {self.last_value:.1f}{unit}[/]",
            border_style=border_color,
            width=width,
            height=height,
            padding=(0, 1),
        )

        self._buffer.seek(0)
        self._buffer.truncate(0)
        self._console.width = width
        self._console.print(panel)
        self.cached_frame = self._buffer.getvalue()
