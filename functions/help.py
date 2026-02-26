import functions.theme.theme_logic

def handle_help_command(log_to_buffer):
    functions.theme.theme_logic.load_theme()
    current_theme = functions.theme.theme_logic.current_theme
    get_pt_color_hex = functions.theme.theme_logic.get_pt_color_hex
    primary_hex = get_pt_color_hex(current_theme["primary"])
    secondary_hex = get_pt_color_hex(current_theme["secondary"])
    
    log_to_buffer("")
    log_to_buffer(f"[bold {primary_hex}]Available commands:[/bold {primary_hex}]")
    log_to_buffer(f"  [bold {secondary_hex}]/theme, /sysinfo, /copy, /quit, /help, /clear[/bold {secondary_hex}]")