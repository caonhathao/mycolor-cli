# AGENTS.md - MYCOLOR CLI Developer Guide

## 1. Project Overview

MYCOLOR CLI is a Python 3.12+ TUI application with system monitoring.
- **Entry Point**: `app/myworld.py`
- **Tech Stack**: `prompt_toolkit`, `rich`, `psutil`
- **Platform**: Windows (requires Windows Terminal for TrueColor)
- **Architecture**: Core-API-UI layered architecture with singleton patterns

## 2. Build, Lint, and Test Commands

```bash
# Run application
run.bat
.venv\Scripts\python.exe app\myworld.py

# Run specific entry points
.venv\Scripts\python.exe app\taskmgr_standalone.py
.venv\Scripts\python.exe app\settings_standalone.py

# Single test
.venv\Scripts\python.exe -m pytest tests\test_file.py::test_function_name -v

# Test file
.venv\Scripts\python.exe -m pytest tests\test_file.py -v

# All tests
.venv\Scripts\python.exe -m pytest

# Syntax check
python -m py_compile path\to\file.py

# Linting (if added)
ruff check .
mypy .
```

## 3. Code Style Guidelines

### General
- Line length: < 120 chars
- Indentation: 4 spaces (no tabs)
- Encoding: UTF-8 (`sys.stdout.reconfigure(encoding='utf-8')`)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `BaseMonitor` |
| Functions/Variables | snake_case | `get_input_text` |
| Constants | UPPER_SNAKE_CASE | `HORIZONTAL = "─"` |
| Private methods | Leading underscore | `_generate_graph` |
| Modules | snake_case | `theme_engine` |

### Imports (3 groups, blank lines between)

```python
import os
import sys

from rich.console import Console

from core.theme_engine import get_current_theme_colors
```

### Types
```python
from typing import List, Optional, Dict, Any

def process_data(data: List[float], max_val: Optional[float] = None) -> Dict[str, Any]:
    ...
```

### Error Handling
- Use specific exception types
- Log critical errors to `logs/mw_crash.log`
- Handle `PermissionError` by closing file handles before rewriting
- Use broad `except` only when error type is unknown

```python
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}
except json.JSONDecodeError as e:
    log_to_buffer(f"[bold red]Config error: {e}[/bold red]")
```

## 4. Rich + prompt_toolkit Integration (CRITICAL)

**Never pass raw Rich objects to prompt_toolkit.** Convert to ANSI first:

```python
def rich_to_ansi(renderable, width=80):
    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=width)
    console.print(renderable)
    return buffer.getvalue()

# prompt_toolkit FormattedText must be list of tuples
[('class:prompt-prefix', ' > '), ('style', 'text')]

# Use ANSI() wrapper
from prompt_toolkit.formatted_text import ANSI
return ANSI(rich_to_ansi(renderable, width))
```

## 5. Theme System (CRITICAL)

Data flow: `config/settings.json` → `core/config_manager.py` → `core/theme_engine.py` → UI

Always use `core.theme_engine`:

```python
from core.theme_engine import get_current_theme_colors

# Fetch EVERY frame in render loops
colors = get_current_theme_colors()
primary = colors.get("primary")      # #A9B7C6 (Darcula)
background = colors.get("background")  # #2B2B2B (Darcula)
```

**DO NOT USE**: `core.constants.THEME_COLORS`, `commands.functions.theme.theme_logic.current_theme`

### Theme Colors

| Theme | Primary | Background | Success | Error |
|-------|---------|-------------|---------|-------|
| darcula | #A9B7C6 | #2B2B2B | #6A8759 | #CC7832 |
| matrix | #00FF41 | #000500 | #00FF41 | #FF0040 |
| cyber | #FF007F | #0f0913 | #00FF00 | #FF0000 |

## 6. Visual & Layout Standards (CRITICAL)

- **Background**: `#2B2B2B` for Darcula (not `#0d1117` terminal black)
- **Centering**: Use `shutil.get_terminal_size()` for dynamic vertical padding
- **Logo**: 2-blocks wide (`██`), horizontal gradients (Cyan → Purple → Pink), mesh shadow (`░`)
- **Footer**: Positioned 1-line gap below Input Box. Format: `[Path] | [PC Name]`
- **Force UTF-8** stdout encoding for proper `██` rendering

## 7. Project Structure

```
E:\ProjectDev\cli\
├── app/                    # Entry points (myworld.py, taskmgr_standalone.py)
├── api/                    # Public API (theme_api.py)
├── commands/               # Command handlers (functions/*, handles/*)
├── config/                 # settings.json
├── core/                   # SINGLE SOURCE OF TRUTH (theme_engine, config_manager)
├── services/monitors/      # System monitors (cpu, ram, gpu, net)
├── template/               # Response templates
├── ui/                     # UI layer (components, layout, screens, styles)
└── run.bat
```

## 8. Workflow Rules

1. Use `.venv/Scripts/python.exe` for all Python execution
2. Test only in Windows Terminal (`wt.exe`) for TrueColor support
3. Auto-fix `ModuleNotFoundError` with `pip install`
4. On startup: force 120x30 window, clear buffer, reset cursor to (0,0)
5. Always check `mw_crash.log` before reporting issues
6. If bug found, apply fix and re-run `run.bat` autonomously

## 9. Adding New Commands

1. Create `commands/functions/mycommand/mycommand_logic.py`
2. Create `commands/functions/mycommand/mycommand_cmd.py`
3. Add handler to `commands/registry.py`
4. Add completions to `ui/components/completer.py`

## 10. Key Singletons

| Singleton | Accessor | Location |
|-----------|---------|----------|
| `ConfigManager` | `get_manager()` | core/config_manager.py |
| `ThemeEngine` | `get_current_theme_colors()` | core/theme_engine.py |
| `SystemDataBridge` | `get_system_bridge()` | api/system_api.py |
| `HistoryTracker` | `get_history_tracker()` | ui/modules/tracker/history_tracker.py |

## 11. Notification System (Global)

Use the global notification system for user feedback:

```python
from ui.layout.notification_layout import get_notification_trigger

trigger = get_notification_trigger()
trigger("Operation successful!", is_success=True)  # Shows green box for 5s
trigger("Error occurred!", is_success=False)        # Shows red box for 5s
```

- Notifications auto-hide after 5 seconds
- Uses `Condition(lambda: show_notification and bool(message.strip()))` filter
- Same visual style across all screens (Main, Settings, Task Manager)

## 12. Common Tasks

| Task | Command |
|------|---------|
| Run app | `run.bat` |
| Syntax check | `python -m py_compile file.py` |
| List themes | `python -c "from core.theme_engine import THEMES; print(list(THEMES.keys()))"` |
| Switch theme | `/theme --style darcula` |

---

*Generated: MYCOLOR CLI Developer Guide (Updated: 2026-04-29)*
