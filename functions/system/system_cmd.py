from .system_logic import terminate_process, run_new_task, set_startup_state, launch_taskmgr_window
import functions.theme.theme_logic
from template.result_response import BaseResponseTemplate

def handle_system_command(log_to_buffer, command_text, app_ref):
    parts = command_text.split()
    flags = parts[1:] if len(parts) > 1 else []
    
    primary_hex = functions.theme.theme_logic.get_pt_color_hex(functions.theme.theme_logic.current_theme["primary"])
    secondary_hex = functions.theme.theme_logic.get_pt_color_hex(functions.theme.theme_logic.current_theme["secondary"])

    if not flags:
        log_to_buffer(BaseResponseTemplate(
            "System Task Manager & Control",
            "/system [flags]",
            {
                "--taskmgr": "Open Interactive Task Manager UI",
                "--end-task <pid>": "Terminate a process by PID",
                "--run-new <cmd>": "Start a new process",
                "--d <name>": "Disable a startup app",
                "--e <name>": "Enable a startup app"
            }
        ))
        return

    if "--taskmgr" in flags:
        success, msg = launch_taskmgr_window()
        if success:
            log_to_buffer(f"[bold {secondary_hex}][System] {msg}[/bold {secondary_hex}]")
        else:
            log_to_buffer(f"[bold red]Error: {msg}[/bold red]")
        return

    if "--end-task" in flags:
        try:
            pid_idx = flags.index("--end-task") + 1
            pid = int(flags[pid_idx])
            success, msg = terminate_process(pid)
            color = "green" if success else "red"
            log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
        except (IndexError, ValueError):
            log_to_buffer(f"[bold red]Error: Missing or invalid PID.[/bold red]")

    if "--run-new" in flags:
        try:
            cmd_idx = flags.index("--run-new") + 1
            cmd = " ".join(flags[cmd_idx:])
            success, msg = run_new_task(cmd)
            color = "green" if success else "red"
            log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
        except IndexError:
            log_to_buffer(f"[bold red]Error: Missing command.[/bold red]")
            
    # Startup management
    for flag, enable in [("--d", False), ("--e", True)]:
        if flag in flags:
            try:
                name_idx = flags.index(flag) + 1
                name = " ".join(flags[name_idx:]) # Assume name is the rest
                success, msg = set_startup_state(name, enable)
                color = "green" if success else "red"
                log_to_buffer(f"[bold {color}]{msg}[/bold {color}]")
                return # Exit after processing one startup command to avoid confusion
            except IndexError:
                log_to_buffer(f"[bold red]Error: Missing app name.[/bold red]")