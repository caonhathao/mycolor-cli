from rich.panel import Panel
from .sysinfo_logic import (
    get_general_info, get_cpu_info, get_ram_info, 
    get_disk_info, get_display_info, get_input_info
)
import functions.theme.theme_logic

def format_output(title, data_dict, log_to_buffer):
    current_theme = functions.theme.theme_logic.current_theme
    get_pt_color_hex = functions.theme.theme_logic.get_pt_color_hex
    primary_hex = get_pt_color_hex(current_theme["primary"])
    secondary_hex = get_pt_color_hex(current_theme["secondary"])
    
    # Spacing before block
    log_to_buffer("")

    # Header
    log_to_buffer(f"[bold {primary_hex}]{title}[/bold {primary_hex}]")

    # Rows
    for key, value in data_dict.items():
        log_to_buffer(f"  [white]{key}:[/white] [bold {secondary_hex}]{str(value)}[/bold {secondary_hex}]")

def handle_sysinfo_command(log_to_buffer, command_text=""):
    parts = command_text.split()
    flags = parts[1:] if len(parts) > 1 else []
    
    current_theme = functions.theme.theme_logic.current_theme
    get_pt_color_hex = functions.theme.theme_logic.get_pt_color_hex
    primary_hex = get_pt_color_hex(current_theme["primary"])
    secondary_hex = get_pt_color_hex(current_theme["secondary"])

    if not flags:
        # Show Guide
        log_to_buffer("")
        help_text = f"""
[{primary_hex} bold]System Information Tool (DxDiag Style)[/{primary_hex} bold]

[bold white]Usage:[/bold white] /sysinfo [flags]

[bold {primary_hex}]Available Flags:[/bold {primary_hex}]
  [{secondary_hex}]--g[/]        General System Information
  [{secondary_hex}]--cpu[/]      Processor Specifications
  [{secondary_hex}]--ram[/]      Memory Statistics
  [{secondary_hex}]--disk[/]     Storage Devices
  [{secondary_hex}]--display[/]  Graphics Devices
  [{secondary_hex}]--input[/]    Peripherals
  [{secondary_hex}]--help[/]     Show this guide
"""
        log_to_buffer(Panel(help_text.strip(), border_style=primary_hex, title="Command Guide", width=80))
        return

    if "--help" in flags:
        handle_sysinfo_command(log_to_buffer, "/sysinfo")
        return

    if "--g" in flags:
        format_output("General Information", get_general_info(), log_to_buffer)
    
    if "--cpu" in flags:
        format_output("Processor Information", get_cpu_info(), log_to_buffer)

    if "--ram" in flags:
        format_output("Memory Information", get_ram_info(), log_to_buffer)

    if "--disk" in flags:
        disks = get_disk_info()
        for i, disk in enumerate(disks):
            format_output(f"Disk {i+1}: {disk['Drive']}", disk, log_to_buffer)

    if "--display" in flags:
        displays = get_display_info()
        if not displays:
             format_output("Display Devices", {"Status": "No display info available"}, log_to_buffer)
        for i, disp in enumerate(displays):
            format_output(f"Display {i+1}", disp, log_to_buffer)

    if "--input" in flags:
        inputs = get_input_info()
        if not inputs:
            format_output("Input Devices", {"Status": "No input info available"}, log_to_buffer)
        else:
            data = {f"{item['Type']} {i+1}": item['Name'] for i, item in enumerate(inputs)}
            format_output("Input Devices", data, log_to_buffer)