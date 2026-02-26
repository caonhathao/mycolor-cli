from rich.table import Table
from .theme_logic import set_theme, get_app_style, THEMES
from template.result_response import BaseResponseTemplate

def handle_theme_command(command_text, log_to_buffer, app_ref):
    parts = command_text.split()
    if len(parts) == 1:
        log_to_buffer(BaseResponseTemplate(
            "Theme Manager",
            "/theme [flags]",
            {
                "--style <name>": "Set a specific theme",
                "--list": "List available themes",
                "-h, --help": "Show this guide"
            }
        ))
    elif len(parts) == 2 and (parts[1] == "--help" or parts[1] == "-h"):
        # Reuse the base template for help as well for consistency
        handle_theme_command("/theme", log_to_buffer, app_ref)
    elif len(parts) == 2 and parts[1] == "--list":
        table = Table(title="Available Themes", show_header=False, box=None)
        table.add_column("Name", style="cyan")
        for name in THEMES.keys():
            table.add_row(name)
        log_to_buffer(table)
    elif len(parts) == 3 and parts[1] == "--style":
        style_name = parts[2]
        if set_theme(style_name):
            app_ref.style = get_app_style()
            log_to_buffer(f"[bold green]Theme set to {style_name}[/bold green]")
        else:
            log_to_buffer(f"[bold red]Error: Theme '{style_name}' not found. Use /theme --list to see options.[/bold red]")
    else:
        log_to_buffer("[bold red]Error: Invalid arguments. Use /theme -h or /theme --help for usage.[/bold red]")