from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import io

class BaseMonitor:
    def __init__(self, title="Monitor", color="green"):
        self.title = title
        self.color = color
        self.history = [0.0] * 100
        self.last_value = 0.0
        self.cached_frame = ""
        # Vertical Column block system as requested
        self.blocks = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']

    def update(self):
        pass

    def get_cached_frame(self):
        return self.cached_frame

    def _get_graph_text(self, data, width, height, color):
        inner_width = max(1, width)
        inner_height = max(1, height)
        
        data_slice = data[-inner_width:]
        if len(data_slice) < inner_width:
            data_slice = [0.0] * (inner_width - len(data_slice)) + data_slice

        graph_rows = [[' ' for _ in range(inner_width)] for _ in range(inner_height)]

        for x, val in enumerate(data_slice):
            # Normalize value (0-100) to height
            h = (val / 100.0) * inner_height
            full_blocks = int(h)
            remainder = h - full_blocks

            # Fill full blocks from bottom
            for y in range(full_blocks):
                row_idx = inner_height - 1 - y
                if 0 <= row_idx < inner_height:
                    graph_rows[row_idx][x] = '█'
            
            # Add partial block
            if remainder > 0 and full_blocks < inner_height:
                idx = int(remainder * 8)
                if idx > 7: idx = 7
                row_idx = inner_height - 1 - full_blocks
                if 0 <= row_idx < inner_height:
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

        graph_text = self._get_graph_text(self.history, inner_width, inner_height, color)

        panel = Panel(
            Align.center(graph_text),
            title=f"[{color}]{self.title}: {self.last_value:.1f}{unit}[/]",
            border_style=border_color,
            width=width,
            height=height,
            padding=(0, 1)
        )

        console = Console(file=io.StringIO(), force_terminal=True, width=width)
        console.print(panel)
        self.cached_frame = console.file.getvalue()