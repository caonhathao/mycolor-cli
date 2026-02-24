import functions.theme.theme_logic


def BaseResponseTemplate(title, usage, flags_dict):
    """
    Returns a formatted string for command responses using the unified borderless style.

    Args:
        title (str): The main header text.
        usage (str): The usage instruction string.
        flags_dict (dict): A dictionary where keys are flags (e.g., "--help") and values are descriptions.
    """
    current_theme = functions.theme.theme_logic.current_theme
    get_pt_color_hex = functions.theme.theme_logic.get_pt_color_hex
    primary_hex = get_pt_color_hex(current_theme["primary"])
    secondary_hex = get_pt_color_hex(current_theme["secondary"])

    # Header
    output = f"[{primary_hex} bold]{title}[/{primary_hex} bold]\n\n"

    # Usage
    output += f"[bold white]Usage:[/bold white] [{secondary_hex} bold]{usage}[/{secondary_hex} bold]\n\n"

    # Flags/Options
    if flags_dict:
        output += f"[bold {primary_hex}]Available Flags:[/bold {primary_hex}]\n"
        for flag, desc in flags_dict.items():
            # 2-space indentation
            output += f"  [{secondary_hex}]{flag}[/]    {desc}\n"

    return output.strip()
