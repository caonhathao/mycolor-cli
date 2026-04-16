# MYCOLOR CLI Project Structure

## 1. Directory Tree

```
E:\ProjectDev\cli\
├── myworld.py                 # Main entry point
├── config.json                # Theme and window settings
├── run.bat                    # Launch script
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
├── AGENTS.md                  # Developer guide
├── mw_crash.log               # Crash reports
├── debug.log                  # Debug logs
├── app_session.log            # Session logs
│
├── components/               # UI widgets
│   ├── __pycache__/
│   ├── completer.py          # Command auto-completion
│   ├── footer.py             # Footer bar (cwd + hostname)
│   ├── input_area.py         # Input TextArea + key bindings + command routing
│   ├── logo.py               # ASCII logo renderer
│   └── tips.py               # Tips display
│
├── functions/                # Command handlers
│   ├── __pycache__/
│   ├── help.py              # /help command handler
│   ├── clear.py             # /clear command handler
│   ├── quit.py              # /quit command handler
│   ├── copy/                # /copy command module
│   │   ├── copy_cmd.py
│   │   └── copy_logic.py
│   ├── sysinfo/             # /sysinfo command module
│   │   ├── sysinfo_cmd.py
│   │   └── sysinfo_logic.py
│   ├── system/              # /system command module
│   │   ├── system_cmd.py
│   │   └── system_logic.py
│   └── theme/               # /theme command module
│       ├── theme_cmd.py
│       └── theme_logic.py
│
├── layout/                   # Layout definitions
│   ├── __pycache__/
│   └── taskmgr_layout.py    # Task manager layout builder
│
├── modules/                   # System monitoring modules
│   ├── __pycache__/
│   ├── panels/
│   │   ├── __pycache__/
│   │   └── detail_panel.py   # Process detail panel
│   ├── tabs/
│   │   ├── __pycache__/
│   │   ├── __init__.py
│   │   ├── base_tab.py       # Base tab class
│   │   ├── performance_tab.py # Performance graphs tab
│   │   ├── processes_tab.py  # Process list tab
│   │   └── startup_tab.py    # Startup apps tab
│   ├── tracker/
│   │   ├── __pycache__/
│   │   └── history_tracker.py # Command result history
│   └── utils/
│       ├── __pycache__/
│       ├── clipboard_manager.py
│       └── gpu_monitor.py
│
├── screens/                   # Screen containers
│   ├── __pycache__/
│   ├── cmd_screen.py         # Command screen (main CLI view)
│   ├── intro_screen.py       # Intro/hero screen
│   └── taskmgr_screen.py    # Task manager interface
│
├── template/                  # Response templates
│   ├── __pycache__/
│   ├── __init__.py
│   └── result_response.py    # BaseResponseTemplate

└── .venv/                     # Virtual environment
```

## 2. Component & File Responsibilities

### Entry Point
| File | Role |
|------|------|
| `myworld.py` | Main application bootstrap, screen routing, prompt_toolkit Application setup, Windows Terminal detection and relaunch |

### Components (UI Widgets)
| File | Role |
|------|------|
| `components/input_area.py` | Creates TextArea widget, defines `accept_input()` command router, manages `log_to_buffer()` for output, key bindings (Ctrl+C, Ctrl+Q, backspace), notification clearing |
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
| `modules/tabs/base_tab.py` | Base class for all tabs |
| `modules/tabs/processes_tab.py` | Process list with selection. Columns: PID(8), Process Name(35), User(15), Threads(10), Handles(10), CPU %(10), Memory %(12). Sorted by PID ascending. Filterable via config.json. |
| `modules/tabs/performance_tab.py` | CPU/RAM/GPU/Network graph monitors |
| `modules/tabs/startup_tab.py` | Startup applications list |
| `modules/panels/detail_panel.py` | Detail panel for selected item |
| `modules/utils/gpu_monitor.py` | GPU monitoring (requires nvidia-ml-py) |
| `modules/utils/clipboard_manager.py` | Clipboard operations |

### Templates
| File | Role |
|------|------|
| `template/result_response.py` | `BaseResponseTemplate` function for standardized command help output |

### Configuration
| File | Role |
|------|------|
| `config.json` | Theme selection, window size, layout visibility, update intervals |

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

### UI Event Bindings

**Key Bindings** (in `components/input_area.py`):
```python
# Ctrl+C and Ctrl+Q - exit app
@kb.add("c-c", eager=True)
@kb.add("c-q", eager=True)
def quit_app(event): event.app.exit()

# Backspace - re-trigger completions
@kb.add("backspace")
def _(event): event.current_buffer.start_completion(select_first=False)
```

**History/Output Key Bindings** (in `screens/cmd_screen.py`):
```python
@kb.add("tab")          # Disabled (pass) - prevents focus switch
@kb.add("pageup")       # Cursor up 10 lines
@kb.add("pagedown")     # Cursor down 10 lines
@kb.add(Keys.ScrollUp)  # Cursor up 5 lines
@kb.add(Keys.ScrollDown") # Cursor down 5 lines
```

**Mouse Events** (in `screens/cmd_screen.py`):
```python
def history_mouse_handler(mouse_event):
    if mouse_event.event_type == MouseEventType.SCROLL_UP:
        output_buffer.buffer.cursor_up(count=20)
    elif mouse_event.event_type == MouseEventType.SCROLL_DOWN:
        output_buffer.buffer.cursor_down(count=20)
    else:
        return NotImplemented  # Selection, right-click DISABLED
```

**Tab Navigation** (in `layout/taskmgr_layout.py`):
```python
@tabs_kb.add("left")    # Previous tab
@tabs_kb.add("right")   # Next tab
@kb.add("up")           # Selection up (non-sidebar tabs)
@kb.add("down")         # Selection down (non-sidebar tabs)
@kb.add("tab")          # Toggle focus between content/tabs
@kb.add("q")            # Quit task manager
```

### Notification System

**Location**: `screens/cmd_screen.py` (lines 62-129)

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

**Trigger from Input** (`components/input_area.py` line 295):
```python
from screens.cmd_screen import get_notification_trigger
notification_trigger = get_notification_trigger()
handle_copy_command(..., notification_trigger, ...)
```

**Rendering** (FloatContainer with ConditionalContainer in cmd_screen.py lines 300-321)

### Task Manager State

**Location**: `modules/tabs/processes_tab.py`

**Process Data**: Fetches via `psutil.process_iter()` with fields: `pid`, `name`, `cpu_percent`, `memory_percent`, `num_threads`, `create_time`, `username`

**Columns** (Fixed widths for alignment):
| Column | Width | Color |
|--------|-------|-------|
| PID | 8 | Cyan (#00FFFF) |
| Process Name | 35 | White |
| User | 15 | Primary theme |
| Threads | 10 | Green (#00FF88) |
| Handles | 10 | Green (#00FF88) |
| CPU % | 10 | Green (#00FF88) |
| Memory % | 12 | Green (#00FF88) |

**Sorting**: Sorted by PID ascending (1, 4, ...)

**Filtering**:
- `show_system_processes` (config.json): When false, hides SYSTEM, LOCAL SERVICE, NETWORK SERVICE users
- `hide_system_exes` (config.json): Additional exe names to filter

**Selection**: `selected_index` tracks highlighted row, navigable via Up/Down keys in taskmgr_layout

### Help Registry

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

### Batch Kill Confirmation Workflow

**Location**: `functions/system/system_cmd.py`

**State Variables**:
- `_pending_kill`: Module-level dict storing `{"name": str, "matches": list}`
- `get_pending_kill()`: Returns pending kill state (or None)
- `set_pending_kill(name, matches)`: Sets pending kill for confirmation
- `clear_pending_kill()`: Clears pending kill state

**Workflow**:
1. User runs `/system --kill <name>`
2. `find_processes_by_name()` searches for matching processes (case-insensitive)
3. If matches found: displays dry-run table (PID, Name, Status, Memory), stores state, prompts for Y/yes
4. If no matches: shows error notification
5. Next user input checked in `input_area.py accept_input()`:
   - "Y" or "yes": Calls `confirm_and_execute_kill()` which runs `kill_processes_by_name()`
   - Any other input: Shows "Operation aborted by user."

**Notification Messages**:
- Success: `"Batch kill completed. N services of Name stopped."`
- Cancel: `"Operation aborted by user."`
- Error: `"No processes found matching 'name'."`

### Process Termination by PID

**Location**: `functions/system/system_logic.py` (`terminate_process()`)

**Implementation**: Uses `taskkill /F /PID <pid>` for forceful termination

**Error Handling**:
- Not found: `"Process ID [PID] not found."`
- Access denied: `"Insufficient privileges to end process [PID]."`
- Generic: Returns stderr message

**Used by**: `/system --end-task <pid>` command

### Formatted Table Output Pattern

**Pattern for ANSI-safe table output** (avoids complex Rich Table rendering issues):
```python
# Use simple f-strings with Rich markup instead of Rich Table
colors = get_current_theme_colors()
primary_hex = colors["primary"]
secondary_hex = colors["secondary"]
pid_color = "#00FFFF"

header = f"[{primary_hex} bold]{'PID':<8} {'Process Name':<35} {'Status':<10} {'Memory':>12}[/{primary_hex} bold]"
log_to_buffer(header)
log_to_buffer(f"[{primary_hex} bold]{'-' * 70}[/{primary_hex} bold]")

for proc in matches:
    row = (
        f"[{pid_color} bold]{proc['pid']:<8}[/{pid_color} bold]"
        f"[white]{proc['name']:<35}[/white]"
        f"[{secondary_hex}]{proc['status']:<10}[/{secondary_hex}]"
        f"[{secondary_hex}]{proc['memory_mb']:>12.1f}[/{secondary_hex}]"
    )
    log_to_buffer(row)
```

**Dynamic Discovery** (lines 39-52): Auto-discovers command modules in `functions/` directory.

**Command Routing** (in `components/input_area.py` `accept_input()` function):
```python
if command_text.startswith("/theme"):   handle_theme_command(...)
elif command_text.startswith("/sysinfo"): handle_sysinfo_command(...)
elif command_text.startswith("/system"):  handle_system_command(...)
elif command_text == "/help":             handle_help_command(...)
elif command_text.startswith("/copy"):    handle_copy_command(...)
elif command_text == "/clear":            handle_clear_command(...)
```

## 4. Configuration & Environment

### config.json Schema

```json
{
    "theme": "darcula",           // string: "classic" | "matrix" | "cyber" | "darcula"
    "window_settings": {
        "cols": 120,               // int: terminal columns
        "lines": 30,               // int: terminal lines
        "auto_resize": true,       // bool
        "force_full_width": true   // bool
    },
    "layout_visibility": {
        "performance": {
            "show_sidebar": false,         // bool
            "rendered_components": ["graphs"]  // array
        }
    },
    "process_update_interval": 3.0,  // float: seconds
    "net_max_speed_mbps": 100,        // float: Mbps
    "last_export_path": "",           // string: last export directory
    "show_system_processes": true,   // bool: show/hide SYSTEM, LOCAL SERVICE, NETWORK SERVICE
    "hide_system_exes": []           // array: additional exe names to hide
}
```

### Path Resolution

**Config Location** (`functions/theme/theme_logic.py`):
1. Primary: `{project_root}/config.json`
2. Fallback: `{APPDATA}/MyWorldCLI/config.json`
3. Ultimate fallback: `{TEMP}/config.json`

```python
def _get_config_path():
    if getattr(sys, "frozen", False):  # PyInstaller .exe mode
        return os.path.join(os.path.dirname(sys.executable), "config.json")
    return os.path.join(project_root, "config.json")

def get_config_dir():
    if frozen: return os.path.dirname(sys.executable)
    return project_root
```

**User Data Path**:
- Falls back to `%APPDATA%\MyWorldCLI\` if project directory is not writable

## 5. Integration Constraints

### UI Library: prompt_toolkit + Rich

**Key Integration Patterns**:

1. **Rich to prompt_toolkit Conversion** (MANDATORY):
```python
import io
from rich.console import Console

def rich_to_ansi(renderable, width=80):
    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=width)
    console.print(renderable)
    return buffer.getvalue()

# Usage:
text_area.content = ANSI(rich_to_ansi(renderable))
```

2. **FormattedText Format**: Must be `list[tuple[str, str]]` of `(style, text)` pairs

3. **Style Dictionary** (`functions/theme/theme_logic.py` `get_app_style()`):
```python
PTStyle.from_dict({
    "app-background": f"bg:{current_theme['background']}",
    "input-field": f"bg:{background} fg:{primary}",
    "completion-menu": f"bg:{suggestion_bg}",
    # ...
})
```

### Disable Native Interactions

**Text Selection in Output** (`screens/cmd_screen.py` line 146):
```python
def history_mouse_handler(mouse_event):
    # ... scroll handling ...
    return NotImplemented  # All other interactions blocked
```

**Tab Focus Switching** (`screens/cmd_screen.py` lines 255-257):
```python
@kb.add("tab")
def _(event):
    pass  # Tab key disabled in cmd screen
```

**Buffer Read-Only** (lines 42, 157):
```python
output_buffer.read_only = True  # After initial setup
output_buffer.buffer.on_text_changed += enforce_buffer_limit
```

### UTF-8 Encoding Requirement

```python
# myworld.py lines 74-80
sys.stdout.reconfigure(encoding="utf-8")
```

### Windows Terminal Requirement

```python
# myworld.py lines 83-106
if platform.system() == "Windows" and not os.environ.get("WT_SESSION"):
    # Relaunch in wt.exe automatically
```

### Window Sizing

```python
# Force 120x30 on startup and in main_app
os.system("mode con: cols=120 lines=30")
```

---

## 6. Performance Benchmarks & Optimizations

### High-Performance Refactoring (2026-04-16)

#### Fix P1: Singleton Console Pattern for `log_to_buffer`
**Location:** `components/input_area.py`

**Problem:** Dual Console object creation on every log call (2x Console + 2x StringIO per invocation).

**Solution:** Module-level cached console and buffer instances with `truncate(0)` + `seek(0)` reuse pattern.

```python
_ANSI_BUFFER = io.StringIO()
_ANSI_CONSOLE = Console(file=_ANSI_BUFFER, force_terminal=True, width=80)
_PLAIN_BUFFER = io.StringIO()
_PLAIN_CONSOLE = Console(file=_PLAIN_BUFFER, force_terminal=True, width=80, color_system=None)

def log_to_buffer(renderable, save_to_history=True):
    _ANSI_BUFFER.seek(0)
    _ANSI_BUFFER.truncate(0)
    _ANSI_CONSOLE.print(renderable)
    ansi_output = _ANSI_BUFFER.getvalue().rstrip()
    # ... history capture using _PLAIN_BUFFER
```

#### Fix P2: Static String Table for Processes
**Location:** `modules/tabs/processes_tab.py`

**Problem:** Rich.Table object rebuilt on every 3-second refresh cycle.

**Solution:** Pre-formatted ANSI strings using f-string padding. Hash-based invalidation skips rendering when data unchanged.

```python
_ANSI_BUFFER = io.StringIO()

def render(self):
    process_hash = hash((len(processes), top_50_pids, top_50_cpu, ...))
    if process_hash == self._cached_process_hash:
        return self._cached_content  # Skip rendering
    
    # F-string column formatting instead of Rich Table
    _ANSI_BUFFER.write(f"[{primary_hex} bold]{'PID':<7} ...\n")
    for p in visible_processes:
        row = f"[{pid_color}]{p['pid']:<7}[/{pid_color}]..."
```

#### Fix P3: Hash-Based Cache Invalidation
**Location:** `screens/cmd_screen.py`

**Problem:** Text comparison for cache invalidation on 2500-line buffer.

**Solution:** Hash-based comparison with cached theme colors per render cycle.

```python
class NotificationState:
    cached_text_hash: int  # Instead of full text comparison

def get_formatted_content():
    text_hash = hash(current_text)
    if text_hash != state.cached_text_hash:
        state.cached_text_hash = text_hash
        state.cached_lines = split_lines(ANSI(current_text))
```

#### Additional: Batch Process Calls
**Location:** `modules/tabs/processes_tab.py`

**Optimization:** Batch process iteration with single `oneshot()` call per process instead of individual attribute access.

```python
process_batch = [p for p in psutil.process_iter(attrs)]
for p in process_batch:
    with p.oneshot():
        info = {"pid": p.pid, "cpu": p.cpu_percent(), ...}
```

#### Theme Color Caching
**Pattern:** Cache `get_current_theme_colors()` result in local variable during single render cycle.

---

*Generated: Project Architecture Audit (Updated: 2026-04-16)*
