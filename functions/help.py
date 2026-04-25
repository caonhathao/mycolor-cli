from modules.constants import SHORTCUTS, SHORTCUT_CLEAR, SHORTCUT_QUIT, SHORTCUT_CLEAR_INPUT, COMMANDS, get_theme_primary, get_theme_secondary, get_theme_color, THEME_COLORS, get_settings, _get_project_root
import os
import json


def handle_help_command(log_to_buffer):
    primary_hex = get_theme_primary()
    secondary_hex = get_theme_secondary()
    table_text = get_theme_color("table_text", "white")
    dim_color = get_theme_color("table_border", "#444444")

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
    log_to_buffer(f"[bold {primary_hex}]--- Configuration (settings.json) ---[/bold {primary_hex}]")
    log_to_buffer("")

    config = get_settings()
    show_system = config.get("show_system_processes", True)
    export_path = config.get("last_export_path", "Not set")
    theme = config.get("customs", {}).get("theme", "matrix")
    interval = config.get("process_update_interval", 0.5)

    log_to_buffer(f"[{table_text}]show_system_processes[/{table_text}] : (bool) Toggle OS tasks in /system ({show_system})")
    log_to_buffer(f"[{table_text}]buffer_limit[/{table_text}]           : (int) Max history lines (2,500)")
    log_to_buffer(f"[{table_text}]theme[/{table_text}]                   : (str) Active UI theme ({theme})")
    log_to_buffer(f"[{table_text}]default_export_path[/{table_text}]  : (str) Default for /copy --export")
    log_to_buffer(f"[{table_text}]process_update_interval[/{table_text}] : (float) Task Manager refresh ({interval}s)")
    log_to_buffer("")
    log_to_buffer("[bold #00FF88]Tip: Use <command> --help for detailed flag descriptions (e.g., /system --help).[/bold #00FF88]")