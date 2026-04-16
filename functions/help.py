from functions.theme.theme_logic import get_current_theme_colors
import os
import json


def handle_help_command(log_to_buffer):
    colors = get_current_theme_colors()
    primary_hex = colors["primary"]
    secondary_hex = colors["secondary"]
    table_text = colors.get("table_text", "white")
    dim_color = colors.get("table_border", "#444444")

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]--- MYWORLD CLI HELP GUIDE ---[/bold {primary_hex}]")
    log_to_buffer("")

    header = f"[bold {primary_hex}]{'Command':<12} {'Description'}[/bold {primary_hex}]"
    log_to_buffer(header)
    log_to_buffer(f"[dim]{'-' * 50}[/dim]")

    commands = [
        ("/theme", "Switch UI color schemes (classic, matrix, cyber, darcula)"),
        ("/sysinfo", "Display hardware specs, CPU, RAM, disk, OS info"),
        ("/copy", "Copy history to clipboard or export to file (--export)"),
        ("/system", "Manage processes & startup apps (Task Manager)"),
        ("/clear", "Flush terminal buffer (up to 2,500 lines)"),
        ("/quit", "Gracefully exit the application"),
    ]

    for cmd, desc in commands:
        log_to_buffer(f"[{table_text}]{cmd:<12}[/{table_text}] {desc}")

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]--- Key Shortcuts ---[/bold {primary_hex}]")
    log_to_buffer("")

    shortcuts = [
        ("Tab", "Switch between Focus/Input"),
        ("Ctrl+C", "Clear current input line"),
        ("Ctrl+L", "Quick trigger for /clear"),
        ("Arrows", "Navigate command history / Task Manager"),
        ("q", "Quick exit from Task Manager"),
    ]

    for key, desc in shortcuts:
        log_to_buffer(f"[{table_text}]{key:<10}[/{table_text}] : {desc}")

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]--- Configuration (config.json) ---[/bold {primary_hex}]")
    log_to_buffer("")

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    show_system = config.get("show_system_processes", True)
    export_path = config.get("last_export_path", "Not set")
    theme = config.get("theme", "darcula")
    interval = config.get("process_update_interval", 3.0)

    log_to_buffer(f"[{table_text}]show_system_processes[/{table_text}] : (bool) Toggle OS tasks in /system ({show_system})")
    log_to_buffer(f"[{table_text}]buffer_limit[/{table_text}]           : (int) Max history lines (2,500)")
    log_to_buffer(f"[{table_text}]theme[/{table_text}]                   : (str) Active UI theme ({theme})")
    log_to_buffer(f"[{table_text}]default_export_path[/{table_text}]  : (str) Default for /copy --export")
    log_to_buffer(f"[{table_text}]process_update_interval[/{table_text}] : (float) Task Manager refresh ({interval}s)")
    log_to_buffer("")
    log_to_buffer("[bold #00FF88]Tip: Use <command> --help for detailed flag descriptions (e.g., /system --help).[/bold #00FF88]")