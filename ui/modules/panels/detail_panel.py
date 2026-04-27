import datetime
import io
import threading
from time import sleep, time

import psutil
from prompt_toolkit.formatted_text import ANSI
from rich.align import Align
from rich.console import Console
from rich.panel import Panel

from ui.modules.constants import get_theme_primary
from ui.modules.constants import get_theme_primary


class DetailPanel:
    def __init__(self):
        self.sys_uptime = "0:00:00"
        self.sys_procs = 0
        self.sys_threads = 0
        self.sys_handles = 0
        self.running = True
        self.lock = threading.Lock()
        self.last_update_time = 0.0
        self.update_interval = 5.0

        # Start background thread for expensive stats (Threads/Handles)
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

    def _monitor_loop(self):
        """Background loop to fetch heavy system stats."""
        while self.running:
            try:
                threads = 0
                handles = 0
                # Efficiently iterate processes. ad_value=0 handles AccessDenied gracefully.
                # 'num_handles' is available on Windows.
                for p in psutil.process_iter(
                    attrs=["num_threads", "num_handles"], ad_value=0
                ):
                    threads += p.info.get("num_threads") or 0
                    handles += p.info.get("num_handles") or 0

                with self.lock:
                    self.sys_threads = threads
                    self.sys_handles = handles
            except psutil.Error:
                pass

            # Sleep in chunks to allow responsive stopping (update every 5s to save CPU)
            for _ in range(50):
                if not self.running:
                    break
                sleep(0.1)

    def update(self):
        """Fast updates called from the main UI loop."""
        current_time = time()
        if current_time - self.last_update_time < self.update_interval:
            return
        self.last_update_time = current_time

        try:
            boot_time = psutil.boot_time()
            uptime_seconds = time() - boot_time

            with self.lock:
                self.sys_uptime = str(datetime.timedelta(seconds=int(uptime_seconds)))
                self.sys_procs = len(psutil.pids())
        except psutil.Error:
            pass

    def render(self, width):
        """Renders the panel content."""
        primary_hex = get_theme_primary()

        with self.lock:
            uptime = self.sys_uptime
            procs = self.sys_procs
            threads = self.sys_threads
            handles = self.sys_handles

        content = f"""
[white]{"Up time":<15}[/]
[bold red]{uptime}[/]

[white]{"Processes":<15}[/]
[bold red]{procs}[/]

[white]{"Threads":<15}[/]
[bold red]{threads}[/]

[white]{"Handles":<15}[/]
[bold red]{handles}[/]
"""
        panel = Panel(
            Align.left(content.strip()),
            title=f"[bold {primary_hex}]Details[/]",
            border_style=primary_hex,
            expand=True,
        )

        buffer = io.StringIO()
        console = Console(file=buffer, force_terminal=True, width=width)
        console.print(panel)
        return ANSI(buffer.getvalue())

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=0.5)
