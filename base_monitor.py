from rich.panel import Panel
from rich.align import Align
from rich.console import Console
import io

class BaseMonitor:
    def __init__(self, title, history_size=100):
        self.title = title
        self.history = [0.0] * history_size
        self.history_size = history_size
        self.blocks = [' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        self.cached_frame = ""

    def update_data(self, value):
        self.history.append(value)
        if len(self.history) > self.history_size:
            self.history.pop(0)

    def get_cached_frame(self):
        return self.cached_frame

    def render(self, width, height, primary_hex, secondary_hex, value_color="red", auto_scale=False, unit="%", formatter=None):
        panel = self.render_graph(width, height, primary_hex, secondary_hex, value_color, auto_scale, unit, formatter)
        console = Console(file=io.StringIO(), force_terminal=True, width=width)
        console.print(panel)
        self.cached_frame = console.file.getvalue()

    def render_graph(self, width, height, primary_hex, secondary_hex, value_color="red", auto_scale=False, unit="%", formatter=None):
        # Content height is panel height minus borders (2)
        height_chars = max(1, height - 2)
        width_chars = max(10, width - 2)
        
        # Slice data
        data = self.history[-width_chars:] if len(self.history) > width_chars else self.history
        
        max_val = 100.0
        if auto_scale:
            max_val = max(data) if data else 1.0
            if max_val == 0: max_val = 1.0

        # 2. Implement Strict Column-Based Rendering
        # Initialize grid with empty spaces
        grid = [[' ' for _ in range(width_chars)] for _ in range(height_chars)]
        
        # Block characters for 0/8 to 8/8 fill
        # Note: U+2581 is ' ', U+2588 is '█'
        blocks = [" ", " ", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

        for x, val in enumerate(data):
            val_clamped = max(0, min(max_val, val))
            ratio = val_clamped / max_val
            
            # Calculate total height in 1/8th blocks
            total_eighths = int(ratio * height_chars * 8)

            for y in range(height_chars):
                # y=0 is top, y=height_chars-1 is bottom
                row_from_bottom = height_chars - 1 - y
                row_base = row_from_bottom * 8
                
                if total_eighths >= row_base + 8:
                    grid[y][x] = blocks[8] # Full block
                elif total_eighths > row_base:
                    remainder = total_eighths - row_base
                    grid[y][x] = blocks[remainder]
                else:
                    grid[y][x] = blocks[0] # Empty

        graph_text = "\n".join("".join(row) for row in grid)
        current_val = data[-1]
        if formatter:
            val_str = formatter(current_val)
        else:
            val_str = f"{current_val:.1f}{unit}"
        
        return Panel(Align.center(f"[{secondary_hex}]{graph_text}[/]"), title=f"[bold {primary_hex}]{self.title}: [bold {value_color}]{val_str}[/][/]", border_style=primary_hex, height=height, width=width)