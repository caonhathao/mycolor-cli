# MYCOLOR CLI Project Structure

## 1. Directory Tree

```
E:\ProjectDev\cli\
├── myworld.py                 # Main entry point
├── config.json              # Theme and window settings
├── run.bat                 # Launch script
├── requirements.txt        # Dependencies
├── README.md              # Documentation
├── AGENTS.md             # Developer guide
├── mw_crash.log           # Crash reports (intentional)
│
├── components/           # UI widgets
│   ├── __init__.py
│   ├── completer.py      # Command auto-completion
│   ├── footer.py        # Footer bar (cwd + hostname)
│   ├── input_area.py   # Input TextArea + key bindings + command routing
│   ├── logo.py        # ASCII logo renderer
│   └── tips.py        # Tips display
│
├── functions/           # Command handlers
│   ├── __init__.py
│   ├── help.py        # /help command handler
│   ├── clear.py      # /clear command handler
│   ├── quit.py      # /quit command handler
│   ├── copy/        # /copy command module
│   │   ├── __init__.py
│   │   ├── copy_cmd.py
│   │   └── copy_logic.py
│   ├── sysinfo/      # /sysinfo command module
│   │   ├── __init__.py
│   │   ├── sysinfo_cmd.py
│   │   └── sysinfo_logic.py
│   ├── system/      # /system command module
│   │   ├── __init__.py
│   │   ├── system_cmd.py
│   │   └── system_logic.py
│   └── theme/      # /theme command module
│       ├── __init__.py
│       ├── theme_cmd.py
│       └── theme_logic.py
│
├── layout/            # Layout definitions
│   ├── __init__.py
│   └── taskmgr_layout.py # Task manager layout builder
│
├── modules/          # System monitoring modules
│   ├── __init__.py
│   ├── monitors/   # System monitors
│   │   ├── __init__.py
│   │   ├── base_monitor.py  # BaseMonitor class
│   │   ├── cpu_monitor.py  # CPU graph monitor
│   │   ├── ram_monitor.py  # RAM graph monitor
│   │   ├── gpu_monitor.py  # GPU graph monitor (nvidia-ml-py)
│   │   └── net_monitor.py  # Network I/O monitor
│   ├── panels/
│   │   ├── __init__.py
│   │   └── detail_panel.py  # Detail panel for selected item
│   ├── tabs/       # Task manager tabs
│   │   ├── __init__.py
│   │   ├── base_tab.py      # BaseTab class
│   │   ├── performance_tab.py # CPU/RAM/GPU graphs tab
│   │   ├── processes_tab.py   # Process list tab
│   │   └── startup_tab.py   # Startup apps tab
│   ├── tracker/
│   │   ├── __init__.py
│   │   └── history_tracker.py # Command result history
│   └── utils/
│       ├── __init__.py
│       └── clipboard_manager.py
│
├── screens/         # Screen containers
│   ├── __init__.py
│   ├── cmd_screen.py     # Command screen (main CLI view)
│   ├── intro_screen.py   # Intro/hero screen
│   └── taskmgr_screen.py # Task manager interface
│
├── template/       # Response templates
│   ├── __init__.py
│   └── result_response.py # BaseResponseTemplate
│
└── .venv/        # Virtual environment
```

## 2. Component & File Responsibilities

### Entry Point
| File | Role |
|------|------|
| `myworld.py` | Main application bootstrap, screen routing, prompt_toolkit Application setup, Windows Terminal detection and relaunch |

### Components (UI Widgets)
| File | Role |
|------|------|
| `components/input_area.py` | Creates TextArea widget, defines `accept_input()` command router, manages `log_to_buffer()` for output, key bindings (Ctrl+C/Q, Alt+Q, Ctrl+L, Alt+C, Ctrl+V, Shift+Up/Down), notification clearing |
| `components/completer.py` | `DynamicCommandCompleter` class - provides tab completion for commands (`/theme`, `/sysinfo`, `/system`, `/copy`, etc.) |
| `components/logo.py` | Generates "MYCOLOR" pixel art ASCII logo with gradient and shadow |
| `components/footer.py` | Footer bar showing current working directory and hostname |
| `components/tips.py` | Displays usage tips on intro screen |

### Screens (Layout Containers)
| File | Role |
|------|------|
| `screens/intro_screen.py` | Hero/intro screen with logo + tips + input area, double-spring centering layout |
| `screens/cmd_screen.py` | Main CLI screen with output buffer, history scrolling, notification toast system, mouse scroll handler |
| `screens/taskmgr_screen.py` | `TaskManagerInterface` class - orchestrates tabs, detail panel, update loop |

### Functions (Command Handlers)
| File | Role |
|------|------|
| `functions/help.py` | Handles `/help` - lists available commands |
| `functions/clear.py` | Handles `/clear` - clears output buffer |
| `functions/quit.py` | Handles `/quit` - exits application |
| `functions/theme/theme_cmd.py` | Parses `/theme` flags, delegates to theme_logic |
| `functions/theme/theme_logic.py` | Theme management (4 themes: classic, matrix, cyber, darcula), config.json loading/saving, prompt_toolkit Style generation |
| `functions/sysinfo/sysinfo_cmd.py` | Parses `/sysinfo` flags, formats output |
| `functions/sysinfo/sysinfo_logic.py` | Gathers CPU, RAM, disk, display, input device info |
| `functions/system/system_cmd.py` | Parses `/system` flags for task manager, handles `--kill` with confirmation state |
| `functions/system/system_logic.py` | Process termination (PID/by-name), app launching, startup management |
| `functions/copy/copy_cmd.py` | Handles `/copy` flags, triggers notifications |
| `functions/copy/copy_logic.py` | History export/copy logic |

### Layout
| File | Role |
|------|------|
| `layout/taskmgr_layout.py` | Builds task manager layout with tabs, graphs, sidebar; key bindings for navigation |

### Modules (Monitors & Utilities)
| File | Role |
|------|------|
| `modules/tracker/history_tracker.py` | `HistoryTracker` class - stores last 10 command-result pairs in memory |
| `modules/monitors/base_monitor.py` | `BaseMonitor` class - abstract base for graph monitors |
| `modules/monitors/cpu_monitor.py` | CPU usage graph monitor |
| `modules/monitors/ram_monitor.py` | RAM usage graph monitor |
| `modules/monitors/gpu_monitor.py` | GPU usage graph monitor (requires nvidia-ml-py) |
| `modules/monitors/net_monitor.py` | Network I/O rate monitor |
| `modules/tabs/base_tab.py` | Base class for all tabs |
| `modules/tabs/processes_tab.py` | Process list with selection |
| `modules/tabs/performance_tab.py` | CPU/RAM/GPU/Network graph monitors |
| `modules/tabs/startup_tab.py` | Startup applications list |
| `modules/panels/detail_panel.py` | Detail panel for selected item |
| `modules/utils/clipboard_manager.py` | Clipboard operations |

### Templates
| File | Role |
|------|------|
| `template/result_response.py` | `BaseResponseTemplate` function for standardized command help output |

### Configuration
| File | Role |
|------|------|
| `config.json` | Theme selection, window size, layout visibility, update intervals |

---

## 3. Core Logic & State Mapping

### Command Buffer (`_result` Storage)
- **Location**: `modules/tracker/history_tracker.py`
- **Class**: `HistoryTracker`
- **Storage**: `self.history` - list of dicts `{"command": str, "result": str}`
- **Max entries**: 10 (oldest auto-removed)
- **Access**: `get_history_tracker()` returns singleton `_history_tracker`

```python
# Usage pattern
from modules.tracker.history_tracker import get_history_tracker
tracker = get_history_tracker()
tracker.start_new_entry(command_text)  # Call on Enter
tracker.append_result(text)            # Append output with newlines
tracker.get_entries()                  # Get all entries
```

### Key Bindings (Input Area)

| Shortcut | Action | Location |
|---------|--------|----------|
| `Ctrl+C` / `Ctrl+Q` | Exit application | input_area.py:464-468 |
| `Alt+Q` | Exit application | input_area.py:470-473 |
| `Ctrl+L` | Clear terminal | input_area.py:475-479 |
| `Alt+C` | Clear input line | input_area.py:485-489 |
| `Ctrl+V` | Paste from clipboard | input_area.py:491-500 |
| `Shift+Up` | History previous | input_area.py:502-507 |
| `Shift+Down` | History next | input_area.py:509-514 |
| `Tab` | Command completion | completer.py |
| `PageUp`/`PageDown` | Output scroll (10 lines) | cmd_screen.py:192-198 |
| `ScrollUp`/`ScrollDown` | Output scroll (5 lines) | cmd_screen.py:200-206 |
| `Mouse Scroll` | Output scroll (20 lines) | cmd_screen.py:138-148 |

### Notification System

**Location**: `screens/cmd_screen.py` (lines 64-129)

**Components**:
- `NotificationState` class - stores `show_notification`, `notification_message`, `notification_task`
- `trigger_notification(message, is_success=True)` - shows toast with 5-second auto-hide
- `clear_notification()` - dismisses current notification

**Access Functions**:
```python
from screens.cmd_screen import get_notification_trigger, get_notification_clearer
get_notification_trigger()()   # Show notification
get_notification_clearer()()  # Clear notification
```

### Help Registry (Dynamic Discovery)

**Location**: `components/completer.py` (`DynamicCommandCompleter.commands` dict)

**Commands**:
```python
self.commands = {
    "/theme": ["--style", "--list", "--help", "-h"],
    "/sysinfo": ["--g", "--cpu", "--ram", "--disk", "--display", "--input", "--help", "-h"],
    "/system": ["--taskmgr", "--end-task", "--kill", "--run-new", "--d", "--e", "--help", "-h"],
    "/copy": ["--last", "--export", "--help", "-h"],
    "/help": [],
    "/quit": [],
    "/clear": [],
}
```

**Dynamic Discovery**: Auto-discovers command modules in `functions/` directory.

### Command Routing

**Location**: `components/input_area.py` `accept_input()` function

```python
if command_text.startswith("/theme"):   handle_theme_command(...)
elif command_text.startswith("/sysinfo"): handle_sysinfo_command(...)
elif command_text.startswith("/system"):  handle_system_command(...)
elif command_text == "/help":             handle_help_command(...)
elif command_text.startswith("/copy"):    handle_copy_command(...)
elif command_text == "/clear":            handle_clear_command(...)
elif command_text.lower() in ("pwd", "ls", "cd", "cls"):
    # Shell command handlers
elif command_text:                     # Execute as shell command
```

### config.json Schema

```json
{
    "theme": "darcula",
    "window_settings": {
        "cols": 120,
        "lines": 30,
        "auto_resize": true,
        "force_full_width": true
    },
    "layout_visibility": {
        "performance": {
            "show_sidebar": false,
            "rendered_components": ["graphs"]
        }
    },
    "process_update_interval": 3.0,
    "net_max_speed_mbps": 100,
    "last_export_path": "",
    "show_system_processes": true,
    "hide_system_exes": []
}
```

---

## 4. Performance Optimizations

### Singleton Console Pattern
**Location**: `components/input_area.py`

Module-level cached console and buffer instances with `truncate(0)` + `seek(0)` reuse pattern.

### Hash-Based Cache Invalidation
**Location**: `screens/cmd_screen.py`, `modules/tabs/processes_tab.py`

Hash-based comparison skips re-rendering when data unchanged.

### Static String Table
**Location**: `modules/tabs/processes_tab.py`

Pre-formatted ANSI strings using f-string padding instead of Rich.Table reconstruction.

### Batch Process Calls
**Location**: `modules/tabs/processes_tab.py`

Single `oneshot()` call per process instead of individual attribute access.

---

*Generated: Project Architecture Audit (Updated: 2026-04-17)*