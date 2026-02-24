import asyncio
import psutil
import socket
import os
import time
import shutil
import json
from prompt_toolkit.formatted_text import ANSI
from rich.table import Table
import datetime
from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
import io

from functions.system.system_logic import get_processes, get_startup_apps
import functions.theme.theme_logic

from prompt_toolkit.layout.dimension import Dimension

class TaskManagerInterface:
    def __init__(self, app):
        self.app = app
        self.active_tab = 0  # 0: Processes, 1: Performance, 2: Startup
        self.focus_mode = "content"  # "content" or "tabs"
        self.selected_index = 0
        self.scroll_offset = 0
        self.processes = []
        self.startup_apps = []
        self.cpu_history = [0.0] * 100
        self.ram_history = [0.0] * 100
        self.gpu_history = [0.0] * 100
        self.net_down_history = [0.0] * 100
        self.net_up_history = [0.0] * 100
        self.sys_uptime = "0:00:00"
        self.sys_procs = 0
        self.sys_threads = 0
        self.sys_handles = 0
        self.running = True
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.last_term_size = shutil.get_terminal_size()
        self.first_render = True
        self.tabs_window = None # Reference to the tabs window for focus checking
        
        # 1. Dimensional Constants & Math
        self.blueprints = self._load_blueprints()
        self.current_mode = "mini" # Default to mini for 120 col launch
        self._apply_blueprint(self.current_mode)
        
        # 1. Mathematical Threshold Calculation
        self.FULL_THRESHOLD = 124
        self.rendered_components = []

        # Adaptive Visibility State
        self.show_sidebar = True
        self._load_initial_visibility()

        # Start background update task
        self.app.create_background_task(self.update_loop())

    def _fetch_stats(self):
        import random

        # psutil calls can be blocking, so we run them in an executor
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        # Mock GPU/Net data for now
        gpu = random.uniform(10, 90)

        # Network Speed Calculation
        curr_net_io = psutil.net_io_counters()
        curr_time = time.time()

        time_delta = curr_time - self.last_net_time
        if time_delta <= 0:
            time_delta = 0.5

        bytes_recv = curr_net_io.bytes_recv - self.last_net_io.bytes_recv
        bytes_sent = curr_net_io.bytes_sent - self.last_net_io.bytes_sent

        down_speed = bytes_recv / time_delta
        up_speed = bytes_sent / time_delta

        self.last_net_io = curr_net_io
        self.last_net_time = curr_time

        # System Details
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))

        proc_count = 0
        thread_count = 0
        handle_count = 0
        for p in psutil.process_iter(['num_threads', 'num_handles']):
            proc_count += 1
            if p.info['num_threads']: thread_count += p.info['num_threads']
            if os.name == 'nt' and p.info['num_handles']: handle_count += p.info['num_handles']

        return cpu, ram, gpu, down_speed, up_speed, uptime_str, proc_count, thread_count, handle_count

    def _load_initial_visibility(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.show_sidebar = config.get("layout_visibility", {}).get("performance", {}).get("show_sidebar", True)
        except Exception:
            self.show_sidebar = True

    def _load_blueprints(self):
        # Fallback defaults
        default_blueprints = {
            "mini": {
                "blocks": {"cpu": {"w": 59, "h": 14}, "details": {"w": 0, "h": 0}},
                "spacers": {"mid_gap": 1, "right_padding": 1}
            },
            "full": {
                "blocks": {"cpu": {"w": 50, "h": 14}, "details": {"w": 22, "h": 28}},
                "spacers": {"mid_gap": 1, "right_padding": 1}
            }
        }
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                return config.get("layout_blueprints", default_blueprints)
        except Exception:
            return default_blueprints

    def _apply_blueprint(self, mode):
        bp = self.blueprints.get(mode, self.blueprints["mini"])
        self.SIDEBAR_WIDTH = bp["blocks"].get("details", {}).get("w", 0)
        self.GRAPH_WIDTH = bp["blocks"]["cpu"]["w"]
        self.GRAPH_HEIGHT = bp["blocks"]["cpu"]["h"]
        self.MID_GAP = bp["spacers"]["mid_gap"]
        self.RIGHT_PADDING = bp["spacers"]["right_padding"]
        self.current_mode = mode

    def _update_config_visibility(self, show_sidebar):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            
            if "layout_visibility" not in config:
                config["layout_visibility"] = {}
            if "performance" not in config["layout_visibility"]:
                config["layout_visibility"]["performance"] = {}
            
            config["layout_visibility"]["performance"]["show_sidebar"] = show_sidebar
            config["layout_visibility"]["performance"]["rendered_components"] = self.rendered_components
            
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
        except Exception:
            pass

    async def update_loop(self):
        loop = asyncio.get_running_loop()
        while self.running:
            # Adaptive Visibility Check
            current_width = shutil.get_terminal_size().columns
            
            # 2. Adaptive Visibility Guard
            new_mode = self.current_mode
            
            if current_width >= self.FULL_THRESHOLD:
                new_mode = "full"
                self.rendered_components = ["graphs", "sidebar"]
            else:
                new_mode = "mini"
                self.rendered_components = ["graphs"]

            if new_mode != self.current_mode:
                self._apply_blueprint(new_mode)
                self.app.renderer.erase() # Ghosting fix
            
            should_show_sidebar = (new_mode == "full")
            if should_show_sidebar != self.show_sidebar:
                self.show_sidebar = should_show_sidebar
                self._update_config_visibility(should_show_sidebar)
                self.app.invalidate()

            # Cleanup Render Artifacts on Resize
            current_term_size = shutil.get_terminal_size()
            if current_term_size != self.last_term_size or self.first_render:
                self.last_term_size = current_term_size
                self.first_render = False
                self.app.renderer.clear()
                self.app.invalidate()

            if self.app.app_state.get("current_screen") == "taskmgr":
                self.processes = get_processes()
                self.startup_apps = list(get_startup_apps().items())

                try:
                    # Fetch stats in background thread to prevent UI lag
                    cpu, ram, gpu, down, up, uptime, procs, threads, handles = await loop.run_in_executor(
                        None, self._fetch_stats
                    )

                    self.cpu_history.append(cpu)
                    self.cpu_history.pop(0)
                    self.ram_history.append(ram)
                    self.ram_history.pop(0)
                    self.gpu_history.append(gpu)
                    self.gpu_history.pop(0)
                    self.net_down_history.append(down)
                    self.net_down_history.pop(0)
                    self.net_up_history.append(up)
                    self.net_up_history.pop(0)

                    self.sys_uptime = uptime
                    self.sys_procs = procs
                    self.sys_threads = threads
                    self.sys_handles = handles

                    self.app.invalidate()
                except Exception:
                    pass
            await asyncio.sleep(0.5)

    def get_header(self):
        primary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["primary"]
        )
        hostname = socket.gethostname()
        return [(f"bg:{primary_hex} fg:#000000 bold", f" SYSTEM MONITOR - {hostname} ")]

    def format_speed(self, bytes_sec):
        if bytes_sec < 1024:
            return f"{bytes_sec:.0f} B/s"
        elif bytes_sec < 1024**2:
            return f"{bytes_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_sec / 1024**2:.1f} MB/s"

    def get_sidebar(self):
        primary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["primary"]
        )
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["secondary"]
        )
        
        content = f"""
[white]{"Up time":<15}[/]
[bold red]{self.sys_uptime}[/]

[white]{"Processes":<15}[/]
[bold red]{self.sys_procs}[/]

[white]{"Threads":<15}[/]
[bold red]{self.sys_threads}[/]

[white]{"Handles":<15}[/]
[bold red]{self.sys_handles}[/]
"""
        panel = Panel(
            Align.left(content.strip()),
            title=f"[bold {primary_hex}]Details[/]",
            border_style=primary_hex,
            expand=True
        )
        
        console = Console(file=io.StringIO(), force_terminal=True, width=self.SIDEBAR_WIDTH)
        console.print(panel)
        return ANSI(console.file.getvalue())

    def _calculate_graph_dimensions(self):
        term_size = shutil.get_terminal_size()
        term_width = term_size.columns
        term_height = term_size.lines

        # Width Calculation
        # Spacers: 1 (mid gap) + 1 (before sidebar/margin) + 1 (right margin) = 3
        spacers_w = 3
        sidebar_w = self.SIDEBAR_WIDTH if self.show_sidebar else 0
        
        available_width = term_width - sidebar_w - spacers_w
        # Split into 2 columns
        quad_width = max(10, available_width // 2)

        # Height Calculation
        # Header(1) + Tabs(1) + Hints(1) + Status(1) = 4
        # Plus 1 vertical spacer in HSplit = 5
        vertical_fixed = 5
        available_height = term_height - vertical_fixed
        quad_height = max(5, available_height // 2)
        
        return quad_width, quad_height

    def _render_graph(self, data, title, value_color, height=None, width=None, auto_scale=False, unit="%", panel_height=None):
        primary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["primary"]
        )
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["secondary"]
        )

        if panel_height is None:
            target_panel_height = self.GRAPH_HEIGHT
        else:
            target_panel_height = panel_height
        
        # Content height is panel height minus borders (2)
        height_chars = max(1, target_panel_height - 2)

        if width:
            width_chars = max(10, width - 2)
        else:
            width_chars = len(data) // 2

        canvas = [0x2800] * (width_chars * height_chars)
        pixel_width = width_chars * 2
        pixel_height = height_chars * 4

        max_val = 100.0
        if auto_scale:
            max_val = max(data) if data else 1.0
            if max_val == 0: max_val = 1.0

        def set_pixel(x, y):
            if not (0 <= x < pixel_width and 0 <= y < pixel_height): return
            char_x = x // 2
            char_y = y // 4
            sub_x = x % 2
            sub_y = y % 4
            dot_mask = 0
            if sub_x == 0:
                dot_mask = [0x01, 0x02, 0x04, 0x40][sub_y]
            else:
                dot_mask = [0x08, 0x10, 0x20, 0x80][sub_y]
            idx = char_y * width_chars + char_x
            if 0 <= idx < len(canvas):
                canvas[idx] |= dot_mask

        prev_y = None
        visible_data = data[-pixel_width:] if len(data) > pixel_width else data
        for x, val in enumerate(visible_data):
            if x >= pixel_width: break
            val_clamped = max(0, min(max_val, val))
            ratio = val_clamped / max_val
            y = int((1.0 - ratio) * (pixel_height - 1))
            if prev_y is not None:
                y_start, y_end = sorted((prev_y, y))
                for curr_y in range(y_start, y_end + 1):
                    set_pixel(x, curr_y)
            else:
                set_pixel(x, y)
            prev_y = y

        rows = []
        for r in range(height_chars):
            row_chars = ""
            for c in range(width_chars):
                row_chars += chr(canvas[r * width_chars + c])
            rows.append(row_chars)
        graph_text = "\n".join(rows)

        current_val = data[-1]
        if auto_scale:
            val_str = self.format_speed(current_val)
        else:
            val_str = f"{current_val:.1f}{unit}"

        return Panel(
            Align.center(f"[{secondary_hex}]{graph_text}[/]"),
            title=f"[bold {primary_hex}]{title}: [bold {value_color}]{val_str}[/][/]",
            border_style=primary_hex,
            height=target_panel_height,
            width=width,
        )

    def get_content(self):
        primary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["primary"]
        )
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["secondary"]
        )
        suggestion_bg = functions.theme.theme_logic.current_theme.get(
            "suggestion_bg", "#21262d"
        )

        # For tables (Processes/Startup), use full available width
        term_width = shutil.get_terminal_size().columns
        console_width = max(10, term_width - 2) # Simple margin
        
        console = Console(file=io.StringIO(), force_terminal=True, width=console_width)

        if self.active_tab == 0:  # Processes
            table = Table(
                show_header=True,
                header_style=f"bold {primary_hex}",
                box=None,
                expand=True,
            )
            table.add_column("PID", width=8, style="dim", no_wrap=True)
            table.add_column("Name", style="white", ratio=1) # Expand Name column
            table.add_column("CPU%", justify="right", style=secondary_hex, width=8)
            table.add_column("MEM%", justify="right", style=secondary_hex, width=8)

            # Thread-safe rendering: Work with a local copy
            current_processes = list(self.processes)

            visible_rows = 20
            max_idx = len(current_processes) - 1
            if self.selected_index > max_idx:
                self.selected_index = max_idx

            # Scrolling logic
            if self.selected_index < self.scroll_offset:
                self.scroll_offset = self.selected_index
            elif self.selected_index >= self.scroll_offset + visible_rows:
                self.scroll_offset = self.selected_index - visible_rows + 1

            for i in range(
                self.scroll_offset,
                min(len(current_processes), self.scroll_offset + visible_rows),
            ):
                try:
                    p = current_processes[i]
                    style = f"on {suggestion_bg}" if i == self.selected_index else ""
                    table.add_row(
                        str(p["pid"]),
                        p["name"],
                        f"{p['cpu_percent']:.1f}",
                        f"{p['memory_percent']:.1f}",
                        style=style,
                    )
                except IndexError:
                    pass

            console.print(table)

        elif self.active_tab == 2:  # Startup
            table = Table(
                show_header=True,
                header_style=f"bold {primary_hex}",
                box=None,
                expand=True,
            )
            table.add_column("App Name", style="white", ratio=1)
            table.add_column("Status", justify="right", width=15)

            for i, (name, info) in enumerate(self.startup_apps):
                style = f"on {suggestion_bg}" if i == self.selected_index else ""
                status = "[green]Enabled[/]" if info["enabled"] else "[red]Disabled[/]"
                table.add_row(name, status, style=style)

            console.print(table)

        return ANSI(console.file.getvalue())

    def _get_graph_content(self, render_func):
        width, height = self._calculate_graph_dimensions()
        console = Console(file=io.StringIO(), force_terminal=True, width=width)
        console.print(render_func(width, height))
        return ANSI(console.file.getvalue())

    def get_cpu(self):
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(functions.theme.theme_logic.current_theme["secondary"])
        return self._get_graph_content(lambda w, h: self._render_graph(self.cpu_history, "CPU", secondary_hex, width=w, panel_height=h))

    def get_ram(self):
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(functions.theme.theme_logic.current_theme["secondary"])
        return self._get_graph_content(lambda w, h: self._render_graph(self.ram_history, "RAM", secondary_hex, width=w, panel_height=h))

    def get_gpu(self):
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(functions.theme.theme_logic.current_theme["secondary"])
        return self._get_graph_content(lambda w, h: self._render_graph(self.gpu_history, "GPU", secondary_hex, width=w, panel_height=h))

    def get_network(self):
        def render(w, h):
            return Group(
                self._render_graph(
                    self.net_down_history,
                    "Download Speed",
                    "red",
                    panel_height=h // 2,
                    width=w,
                    auto_scale=True,
                ),
                self._render_graph(
                    self.net_up_history,
                    "Upload Speed",
                    "red",
                    panel_height=h // 2,
                    width=w,
                    auto_scale=True,
                ),
            )
        return self._get_graph_content(render)

    def get_tabs_control(self):
        primary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["primary"]
        )
        secondary_hex = functions.theme.theme_logic.get_pt_color_hex(
            functions.theme.theme_logic.current_theme["secondary"]
        )
        tabs = ["Processes", "Performance", "Startup"]
        text = []
        for i, tab in enumerate(tabs):
            # 3. Visual Feedback Sync: Check physical focus
            is_focused = False
            if self.tabs_window:
                is_focused = self.app.layout.has_focus(self.tabs_window)

            if i == self.active_tab:
                if is_focused:
                    # Focused state: Bold Yellow (high contrast) for selection mode
                    text.append((f"bg:#ffff00 fg:#000000 bold", f" [{tab}] "))
                else:
                    # Active state: Matrix Green (standard active)
                    text.append((f"bg:{primary_hex} fg:#000000 bold", f" [{tab}] "))
            else:
                text.append(("class:tab", f" {tab} "))
            text.append(("", "   "))
        return text

    def get_hints(self):
        is_focused = False
        if self.tabs_window:
            is_focused = self.app.layout.has_focus(self.tabs_window)
            
        if is_focused:
            return [("class:footer-pad", " Left/Right: Switch Tab | Tab: Return to Content ")]
        else:
            return [("class:footer-pad", " q: Quit | Tab: Focus Tabs | Arrows: Navigate ")]

    def get_status_bar(self):
        return [("class:status", f" E:\\ProjectDev\\cli | LAPTOP-J2I22MSG | v0.0.1 ")]
