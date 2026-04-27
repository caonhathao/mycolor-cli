import os
import json
from template.result_response import BaseResponseTemplate
from core.theme_engine import get_current_theme_colors
from .copy_logic import copy_last_n_pairs, export_history_to_file


def handle_copy_command(command_text, log_func, output_buffer, notification_trigger):
    parts = command_text.strip().split()

    # 1. No arguments or Help -> Show Usage Guide (No notification)
    if len(parts) == 1 or "--help" in parts or "-h" in parts:
        flags = {
            "--last <1-3>": "Copy last N command-result pairs to clipboard (default: 1)",
            "--export <path>[optional]": "Export all history to a file",
            "-h, --help": "Show this guide",
        }

        # Generate base response
        base_output = BaseResponseTemplate("Copy Manager", "/copy [flags]", flags)

        log_func(base_output)
        return

    # 2. Export
    if "--export" in parts:
        _handle_export(parts, log_func, output_buffer, notification_trigger)
        return

    # 3. Last
    if "--last" in parts:
        _handle_last(parts, log_func, notification_trigger)
        return

    # Unknown args
    colors = get_current_theme_colors()
    error_color = colors.get("error", "#CC7832")
    log_func(f"[bold {error_color}]Invalid arguments.[/bold {error_color}]")
    handle_copy_command("/copy --help", log_func, output_buffer, notification_trigger)


def _handle_export(parts, log_func, output_buffer, notification_trigger):
    colors = get_current_theme_colors()
    success_color = colors.get("success", "#6A8759")
    error_color = colors.get("error", "#CC7832")
    
    user_path = None
    try:
        idx = parts.index("--export")
        if idx + 1 < len(parts) and not parts[idx + 1].startswith("-"):
            user_path = parts[idx + 1]
    except ValueError:
        pass

    # Config handling
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(base_dir, "config", "settings.json")
    config = {}

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Cảnh báo: Không thể đọc file config do lỗi: {e}")

    success, message, final_path = export_history_to_file(user_path)

    if success:
        abs_path = os.path.abspath(str(final_path))
        log_func(f"[{success_color}]{abs_path}[/{success_color}]")
        if notification_trigger:
            notification_trigger(
                f"Export successful! Path: {abs_path}", is_success=True
            )
    else:
        if notification_trigger:
            notification_trigger(message, is_success=False)
        else:
            log_func(f"[bold {error_color}]{message}[/bold {error_color}]")


def _handle_last(parts, log_func, notification_trigger):
    colors = get_current_theme_colors()
    success_color = colors.get("success", "#6A8759")
    error_color = colors.get("error", "#CC7832")
    
    count = 1
    try:
        idx = parts.index("--last")
        if idx + 1 < len(parts):
            try:
                val = int(parts[idx + 1])
                if 1 <= val <= 3:
                    count = val
            except ValueError:
                pass
    except ValueError:
        pass

    success, message = copy_last_n_pairs(count)

    if success:
        if notification_trigger:
            notification_trigger("Copied successfully", is_success=True)
        else:
            log_func(f"[{success_color}]{message}[/{success_color}]")
    else:
        if notification_trigger:
            notification_trigger(message, is_success=False)
        else:
            log_func(f"[bold {error_color}]{message}[/bold {error_color}]")
