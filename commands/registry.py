from commands.handles.help import handle_help_command
from commands.handles.clear import handle_clear_command
from commands.handles.quit import handle_quit_command
from commands.functions.theme.theme_cmd import handle_theme_command
from commands.functions.sysinfo.sysinfo_cmd import handle_sysinfo_command
from commands.functions.system.system_cmd import (
    handle_system_command,
    get_pending_kill,
    confirm_and_execute_kill,
)
from commands.functions.copy.copy_cmd import handle_copy_command
from commands.functions.system.system_logic import launch_settings_window
from core.theme_engine import get_current_theme_colors


def dispatch(
    command_text: str,
    log_to_buffer,
    output_buffer,
    application_ref,
    notification_trigger=None,
):
    colors = get_current_theme_colors()
    success_color = colors.get("success", "#6A8759")
    error_color = colors.get("error", "#CC7832")
    primary_hex = colors.get("primary")

    if command_text == "/quit":
        application_ref.exit()
        return True

    elif command_text.startswith("/theme"):
        handle_theme_command(command_text, log_to_buffer, application_ref)
        return True

    elif command_text.startswith("/sysinfo"):
        handle_sysinfo_command(log_to_buffer, command_text)
        return True

    elif command_text.startswith("/system"):
        handle_system_command(log_to_buffer, command_text, notification_trigger)
        return True

    elif command_text == "/help":
        handle_help_command(log_to_buffer)
        return True

    elif command_text.startswith("/settings"):
        if "--help" in command_text or "-h" in command_text:
            log_to_buffer("")
            log_to_buffer(f"[bold {primary_hex}]--- Settings UI ---[/bold {primary_hex}]")
            log_to_buffer("")
            log_to_buffer("[bold]Usage:[/bold] /settings")
            log_to_buffer("")
            log_to_buffer("Opens a standalone window to manage:")
            log_to_buffer("  - Customs: theme, logo style, tips visibility")
            log_to_buffer("  - Shortcuts: keyboard shortcut mappings")
            log_to_buffer("  - Commands: command aliases")
            log_to_buffer("")
            log_to_buffer("[bold #00FF88]Tip: Alt+S saves changes, Alt+Q quits without saving.[/bold #00FF88]")
        else:
            success, msg = launch_settings_window()
            color = success_color if success else error_color
            log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
        return True

    elif command_text.startswith("/copy"):
        handle_copy_command(
            command_text,
            log_to_buffer,
            output_buffer,
            notification_trigger,
        )
        return True

    elif command_text == "/clear" or command_text.lower() in ("cls", "clear"):
        handle_clear_command(output_buffer)
        return True

    return False


def check_pending_confirmation(command_text: str, log_to_buffer):
    pending = get_pending_kill()
    if pending:
        cmd_lower = command_text.lower().strip()
        if cmd_lower in ("y", "yes"):
            confirm_and_execute_kill(log_to_buffer)
            return True
        else:
            log_to_buffer("[bold yellow]Operation aborted by user.[/bold yellow]")
            return True
    return False


def is_help_request(command_text: str) -> bool:
    help_patterns = [
        ("/theme", [" -h ", " -h", " --help", " --help"]),
        ("/system", [" -h ", " -h", " --help", " --help"]),
        ("/sysinfo", [" -h ", " -h", " --help", " --help"]),
        ("/copy", [" -h ", " -h", " --help", " --help"]),
    ]

    for prefix, suffixes in help_patterns:
        if command_text.startswith(prefix):
            for suffix in suffixes:
                if suffix in command_text:
                    return True
            if command_text == prefix + " -h" or command_text == prefix + " --help":
                return True

    return False