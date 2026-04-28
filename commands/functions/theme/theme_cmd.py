from rich.table import Table

from template.result_response import BaseResponseTemplate

from .theme_logic import THEMES, set_theme, get_current_theme_colors


def handle_theme_command(command_text, log_to_buffer, app_ref):
    parts = command_text.split()
    colors = get_current_theme_colors()
    success_color = colors.get("success", "#6A8759")
    error_color = colors.get("error", "#CC7832")
    primary_hex = colors.get("primary")

    if len(parts) == 1 or (len(parts) == 2 and (parts[1] in ["--help", "-h"])):
        log_to_buffer(BaseResponseTemplate(
            "Theme Manager",
            "/theme [flags]",
            {
                "--style <name>": "Set a specific theme (applied after restart)",
                "--list": "List available themes",
                "-h, --help": "Show this guide"
            }
        ))
    elif len(parts) == 2 and parts[1] == "--list":
        table = Table(title="Available Themes", show_header=False, box=None)
        table.add_column("Name", style=primary_hex)
        for name in THEMES.keys():
            table.add_row(name)
        log_to_buffer(table)
    elif len(parts) == 3 and parts[1] == "--style":
        style_name = parts[2]
        if set_theme(style_name):
            log_to_buffer(f"[bold {success_color}]Theme '{style_name}' saved! Changes will be applied after restarting the application.[/bold {success_color}]")
        else:
            log_to_buffer(f"[bold {error_color}]Error: Theme '{style_name}' not found. Use /theme --list to see options.[/bold {error_color}]")
    else:
        log_to_buffer(f"[bold {error_color}]Error: Invalid arguments. Use /theme -h or /theme --help for usage.[/bold {error_color}]")