from functions.theme.theme_logic import get_current_theme_colors


def handle_help_command(log_to_buffer):
    colors = get_current_theme_colors()
    primary_hex = colors["primary"]
    secondary_hex = colors["secondary"]

    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]Available commands:[/bold {primary_hex}]")
    log_to_buffer(f"  [bold {secondary_hex}]/theme, /sysinfo, /copy, /quit, /help, /clear[/bold {secondary_hex}]")