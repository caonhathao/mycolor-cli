import os
import json
from template.result_response import BaseResponseTemplate
from .copy_logic import copy_last_n_pairs, export_history_to_file


def handle_copy_command(command_text, log_func, output_buffer, notification_trigger):
    parts = command_text.strip().split()

    # 1. No arguments or Help -> Show Usage Guide (No notification)
    if len(parts) == 1 or "--help" in parts or "-h" in parts:
        flags = {
            "--last <1-3>": "Copy last N command-result pairs to clipboard (default: 1)",
            "--export <path>[optional]": "Export history to a .txt file. (Default: Documents/mycolor)",
            "-h, --help": "Show this guide"
        }

        # Generate base response
        base_output = BaseResponseTemplate(
            "Copy Manager", "/copy [flags]", flags
        )

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
    log_func("[bold red]Invalid arguments.[/bold red]")
    handle_copy_command("/copy --help", log_func, output_buffer, notification_trigger)


def _handle_export(parts, log_func, output_buffer, notification_trigger):
    user_path = None
    try:
        idx = parts.index("--export")
        if idx + 1 < len(parts) and not parts[idx + 1].startswith("-"):
            user_path = parts[idx + 1]
    except ValueError:
        pass

    # Config handling
    config_path = "config.json"
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
        except:
            pass

    success, message, final_path = export_history_to_file(user_path)

    if success:
        abs_path = os.path.abspath(final_path)
        log_func(f"[green]{abs_path}[/green]")
        if notification_trigger:
            notification_trigger(f"Export successful! Path: {abs_path}", is_success=True)
    else:
        if notification_trigger:
            notification_trigger(message, is_success=False)
        else:
            log_func(f"[bold red]{message}[/bold red]")


def _handle_last(parts, log_func, notification_trigger):
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
            log_func(f"[green]{message}[/green]")
    else:
        if notification_trigger:
            notification_trigger(message, is_success=False)
        else:
            log_func(f"[bold red]{message}[/bold red]")
