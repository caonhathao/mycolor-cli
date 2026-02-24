from rich.table import Table
from rich.panel import Panel
from .theme_logic import set_theme, get_app_style, THEMES
import functions.theme.theme_logic

def handle_theme_command(command_text, log_to_buffer, app_ref):
    current_theme = functions.theme.theme_logic.current_theme
    get_pt_color_hex = functions.theme.theme_logic.get_pt_color_hex
    primary_hex = get_pt_color_hex(current_theme["primary"])
    secondary_hex = get_pt_color_hex(current_theme["secondary"])

    parts = command_text.split()
    if len(parts) == 1:
        log_to_buffer("[bold yellow]Usage: /theme [flags][/bold yellow]")
        log_to_buffer(f"  --style [{secondary_hex}]<name>[/{secondary_hex}]  : Set a specific theme")
        log_to_buffer("  --list          : List available themes")
        log_to_buffer("  --help          : Show detailed help")
    elif len(parts) == 2 and parts[1] == "--help":
        help_content = f"""
[{primary_hex} bold]Description:[/{primary_hex} bold]
  Manage the visual theme of the application.

[bold {primary_hex}]Flags:[/bold {primary_hex}]
  [{secondary_hex}]--style <name>[/{secondary_hex}]  Apply a specific color theme immediately.
  [{secondary_hex}]--list[/{secondary_hex}]          Show a table of all available themes.
  [{secondary_hex}]--help[/{secondary_hex}]          Show this manual.

[bold {primary_hex}]Examples:[/bold {primary_hex}]
  /theme --style cyber
  /theme --list"""
        log_to_buffer(Panel(help_content.strip(), title="[bold magenta]Command Manual: /theme[/bold magenta]", border_style="cyan"))
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
        log_to_buffer("[bold red]Error: Invalid arguments. Use /theme --help for usage.[/bold red]")