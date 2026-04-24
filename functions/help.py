from functions.theme.theme_logic import get_current_theme_colors
from modules.constants import SHORTCUTS, SHORTCUT_CLEAR, SHORTCUT_QUIT, SHORTCUT_CLEAR_INPUT, COMMANDS, get_theme_primary, get_theme_secondary, get_theme_color, THEME_COLORS
import os
import json


def handle_help_command(log_to_buffer):
    colors = get_current_theme_colors()
    primary_hex = colors["primary"]
    secondary_hex = colors["secondary"]
    table_text = colors.get("table_text", "white")
    dim_color = colors.get("table_border", "#444444")

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]--- COMMANDS ---[/bold {primary_hex}]")
    log_to_buffer("")

    command_list = [
        ("/theme", "Switch UI color schemes (classic, matrix, cyber, darcula)"),
        ("/sysinfo", "Display hardware specs, CPU, RAM, disk, OS info"),
        ("/copy", "Copy history to clipboard or export to file (--export)"),
        ("/system", "Manage processes & startup apps (Task Manager)"),
        ("/settings", "Open Settings UI to customize shortcuts & commands"),
        ("/clear", "Flush terminal buffer"),
        ("/quit", "Gracefully exit the application"),
    ]

    for cmd, desc in command_list:
        log_to_buffer(f"[{table_text}]{cmd:<12}[/{table_text}] {desc}")

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]--- Key Shortcuts ---[/bold {primary_hex}]")
    log_to_buffer("")

    shortcuts_list = [
        ("Shift+Up/Down", "Navigate command history"),
        ("Up/Down", "Navigate suggestion menu"),
        ("Alt+C", "Clear current input line"),
        ("Ctrl+V", "Paste text to input"),
        ("Ctrl+L", "Quick trigger for /clear"),
        ("Alt+Q", "Quick trigger for /quit"),
    ]

    for key, desc in shortcuts_list:
        log_to_buffer(f"[{table_text}]{key:<10}[/{table_text}] : {desc}")

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]--- Configuration (config.json) ---[/bold {primary_hex}]")
    log_to_buffer("")

    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.json")
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