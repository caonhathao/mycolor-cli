from core.theme_engine import get_current_theme_colors, get_current_theme


def BaseResponseTemplate(title, usage, flags_dict):
    """
    Returns a formatted string for command responses using the unified borderless style.

    Args:
        title (str): The main header text.
        usage (str): The usage instruction string.
        flags_dict (dict): A dictionary where keys are flags (e.g., "--help") and values are descriptions.
    """
    colors = get_current_theme_colors()
    theme = get_current_theme()
    primary_hex = colors.get("primary")
    secondary_hex = colors.get("secondary")

    # Header
    output = f"[{primary_hex} bold]{title}[/{primary_hex} bold]\n\n"

    # Usage
    output += f"[bold white]Usage:[/bold white] [{secondary_hex} bold]{usage}[/{secondary_hex} bold]\n\n"

    # Flags/Options
    if flags_dict:
        output += f"[bold {primary_hex}]Available Flags:[/bold {primary_hex}]\n"
        
        # Calculate max width for dynamic alignment
        max_flag_width = 0
        for flag in flags_dict.keys():
            max_flag_width = max(max_flag_width, len(flag))
        
        gap = 4

        for flag, desc in flags_dict.items():
            padding = " " * (max_flag_width - len(flag) + gap)
            output += f"  [{secondary_hex}]{flag}[/{secondary_hex}]{padding}[white]{desc}[/white]\n"

    return output.strip()
