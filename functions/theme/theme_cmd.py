from rich.table import Table

from template.result_response import BaseResponseTemplate

from .theme_logic import THEMES, get_app_style, get_current_theme_colors, set_theme


def handle_theme_command(command_text, log_to_buffer, app_ref):
    parts = command_text.split()
    colors = get_current_theme_colors()
    success_color = colors.get("success", "green")
    error_color = colors.get("error", "red")
    primary_hex = colors.get("primary")

    if len(parts) == 1 or (len(parts) == 2 and (parts[1] in ["--help", "-h"])):
        log_to_buffer(BaseResponseTemplate(
            "Theme Manager",
            "/theme [flags]",
            {
                "--style <name>": "Set a specific theme",
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
            app_ref.style = get_app_style()
            new_colors = get_current_theme_colors()
            success = new_colors.get("success", "green")
            log_to_buffer(f"[bold {success}]Theme set to {style_name}[/bold {success}]")
            app_ref.invalidate()
        else:
            log_to_buffer(f"[bold {error_color}]Error: Theme '{style_name}' not found. Use /theme --list to see options.[/bold {error_color}]")
    else:
        log_to_buffer(f"[bold {error_color}]Error: Invalid arguments. Use /theme -h or /theme --help for usage.[/bold {error_color}]")