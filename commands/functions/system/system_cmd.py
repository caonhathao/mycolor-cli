from core.theme_engine import get_current_theme_colors

from template.result_response import BaseResponseTemplate

from .system_logic import (
    find_processes_by_name,
    kill_processes_by_name,
    launch_taskmgr_window,
    launch_settings_window,
    run_new_task,
    set_startup_state,
    terminate_process,
)

_pending_kill = None


def get_pending_kill():
    return _pending_kill


def set_pending_kill(name, matches):
    global _pending_kill
    _pending_kill = {"name": name, "matches": matches}


def clear_pending_kill():
    global _pending_kill
    _pending_kill = None


def confirm_and_execute_kill(log_to_buffer, notification_trigger=None):
    global _pending_kill
    if not _pending_kill:
        return False

    colors = get_current_theme_colors()
    success_color = colors.get("success")
    error_color = colors.get("error")

    name = _pending_kill["name"]
    matches = _pending_kill["matches"]
    _pending_kill = None

    killed, failed, total = kill_processes_by_name(name)
    if killed > 0:
        msg = f"Batch kill completed. {killed} services of {name} stopped."
    else:
        msg = f"No processes were terminated. {total} found but failed to kill."

    if notification_trigger:
        notification_trigger(msg, is_success=(killed > 0))
    else:
        color = success_color if killed > 0 else error_color
        log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
    return True


def handle_system_command(log_to_buffer, command_text, notification_trigger=None):
    parts = command_text.split()
    flags = parts[1:] if len(parts) > 1 else []

    colors = get_current_theme_colors()
    secondary_hex = colors.get("secondary")
    success_color = colors.get("success")
    error_color = colors.get("error")

    if not flags or "-h" in flags or "--help" in flags:
        log_to_buffer(BaseResponseTemplate(
            "System Task Manager & Control",
            "/system [flags]",
            {
                "--taskmgr": "Open Interactive Task Manager UI",
                "--end-task <pid>": "Terminate a process by its Process ID (PID)",
                "--kill <name>": "Kill all processes matching name (dry-run + confirm)",
                "--run-new <cmd>": "Start a new process",
                "--d <name>": "Disable a startup app",
                "--e <name>": "Enable a startup app",
                "-h, --help": "Show this guide"
            }
        ))
        return

    if "--taskmgr" in flags:
        success, msg = launch_taskmgr_window()
        if success:
            log_to_buffer(f"[bold {secondary_hex}][System] {msg}[/bold {secondary_hex}]")
        else:
            log_to_buffer(f"[bold {error_color}]Error: {msg}[/bold {error_color}]")
        return

    if "--end-task" in flags:
        try:
            pid_idx = flags.index("--end-task") + 1
            pid = int(flags[pid_idx])
            success, msg = terminate_process(pid)
            if notification_trigger:
                notification_trigger(msg, is_success=success)
            else:
                color = success_color if success else error_color
                log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
        except (IndexError, ValueError):
            error_msg = f"Error: Missing or invalid PID."
            if notification_trigger:
                notification_trigger(error_msg, is_success=False)
            else:
                log_to_buffer(f"[bold {error_color}]{error_msg}[/bold {error_color}]")
        return

    if "--kill" in flags:
        try:
            kill_idx = flags.index("--kill") + 1
            name = " ".join(flags[kill_idx:])
            if not name:
                log_to_buffer(f"[bold {error_color}]Error: Missing process name.[/bold {error_color}]")
                return

            matches = find_processes_by_name(name)

            if not matches:
                error_msg = f"No processes found matching '{name}'."
                if notification_trigger:
                    notification_trigger(error_msg, is_success=False)
                else:
                    log_to_buffer(f"[bold {error_color}]{error_msg}[/bold {error_color}]")
                return

            colors = get_current_theme_colors()
            primary_hex = colors.get("primary")
            secondary_hex = colors.get("secondary")
            pid_color = secondary_hex

            log_to_buffer("")

            header = f"[{primary_hex} bold]{'PID':<8} {'Process Name':<35} {'Status':<10} {'Memory (MB)':>12}[/{primary_hex} bold]"
            log_to_buffer(header)
            log_to_buffer(f"[{primary_hex} bold]{'-' * 75}[/{primary_hex} bold]")

            for proc in matches:
                row = (
                    f"[{pid_color} bold]{proc['pid']:<8}[/{pid_color} bold]"
                    f"[white]{proc['name']:<35}[/white]"
                    f"[{secondary_hex}]{proc['status']:<10}[/{secondary_hex}]"
                    f"[{secondary_hex}]{proc['memory_mb']:>12.1f}[/{secondary_hex}]"
                )
                log_to_buffer(row)

            log_to_buffer("")
            log_to_buffer(f"[bold {error_color}]Warning: The following {len(matches)} process(es) will be terminated.[/bold {error_color}]")
            log_to_buffer(f"[bold {error_color}]Do you want to proceed? Type 'Y' or 'yes' to confirm.[/bold {error_color}]")
            log_to_buffer("")

            set_pending_kill(name, matches)

        except IndexError:
            log_to_buffer(f"[bold {error_color}]Error: Missing process name.[/bold {error_color}]")

    if "--run-new" in flags:
        try:
            cmd_idx = flags.index("--run-new") + 1
            cmd = " ".join(flags[cmd_idx:])
            success, msg = run_new_task(cmd)
            color = success_color if success else error_color
            log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
        except IndexError:
            log_to_buffer(f"[bold {error_color}]Error: Missing command.[/bold {error_color}]")

    # Startup management
    for flag, enable in [("--d", False), ("--e", True)]:
        if flag in flags:
            try:
                name_idx = flags.index(flag) + 1
                name = " ".join(flags[name_idx:])
                success, msg = set_startup_state(name, enable)
                color = success_color if success else error_color
                log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
                return
            except IndexError:
                log_to_buffer(f"[bold {error_color}]Error: Missing app name.[/bold {error_color}]")
