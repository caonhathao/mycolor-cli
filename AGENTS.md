# AGENTS.md - MYCOLOR CLI Developer Guide

This document provides guidelines for AI agents working on the MYCOLOR CLI project.

## 1. Project Overview

MYCOLOR CLI is a Python-based Terminal User Interface (TUI) application that provides a vibrant, premium command-line experience with system monitoring capabilities.

- **Language**: Python 3.12+
- **Entry Point**: `app/myworld.py`
- **Tech Stack**: `prompt_toolkit` (UI), `rich` (styling), `psutil` (system metrics)
- **Platform**: Windows (primary), requires Windows Terminal for TrueColor support

## 2. Build, Lint, and Test Commands

### Running the Application

```cmd
run.bat
```

Or directly with the virtual environment:

```cmd
.venv\Scripts\python.exe app\myworld.py
```

### Running Specific Entry Points

```cmd
.venv\Scripts\python.exe app\taskmgr_standalone.py    # Task Manager
.venv\Scripts\python.exe app\settings_standalone.py   # Settings UI
```

### Linting and Type Checking

This project does not have a configured linter or type checker. If you add one, prefer:
- `ruff` for fast linting: `ruff check .`
- `mypy` for type checking: `mypy .`

### Running a Single Test

```cmd
.venv\Scripts\python.exe -m pytest tests\test_file.py::test_function_name -v
```

Or run a specific test file:

```cmd
.venv\Scripts\python.exe -m pytest tests\test_file.py -v
```

To run all tests:

```cmd
.venv\Scripts\python.exe -m pytest
```

### Syntax Checking (Python Compile)

```cmd
.venv\Scripts\python.exe -m py_compile path\to\file.py
```

## 3. Code Style Guidelines

### General Conventions

- **Line Length**: Keep lines under 120 characters when practical
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8 (use `sys.stdout.reconfigure(encoding='utf-8')` for cross-shell compatibility)
- **Line Endings**: LF (Unix-style) preferred

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `BaseMonitor`, `DynamicCommandCompleter` |
| Functions/Variables | snake_case | `get_input_text_area`, `handle_help_command` |
| Constants | UPPER_SNAKE_CASE | `HORIZONTAL = "─"` |
| Private methods | Leading underscore | `_generate_graph_text` |
| Module names | snake_case | `theme_engine`, `input_area` |

### Imports

Order imports in the following groups (separated by blank lines):

1. Standard library (`os`, `sys`, `json`, `asyncio`)
2. Third-party libraries (`rich`, `prompt_toolkit`)
3. Custom modules - use absolute imports from project root

```python
import os
import sys
import asyncio

from rich.console import Console
from rich.panel import Panel

from core.theme_engine import get_current_theme_colors
from ui.components.input_area import get_input_text_area
```

### Types

The codebase does not currently use type hints extensively, but when adding new code:
- Use type hints for function signatures and return types
- Prefer `typing` module for complex types (`List`, `Dict`, `Optional`, `Union`)

```python
from typing import List, Optional, Dict, Any

def process_data(data: List[float], max_val: Optional[float] = None) -> Dict[str, Any]:
    ...
```

### Error Handling

- Use try/except blocks with specific exception types when possible
- For critical operations that crash the app, catch and log to `logs/mw_crash.log`
- Handle `PermissionError` by closing file handles before rewriting
- Use broad `except Exception` only when error type is truly unknown

```python
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}
except json.JSONDecodeError as e:
    log_to_buffer(f"[bold red]Config error: {e}[/bold red]")
```

### Rich and prompt_toolkit Integration

**CRITICAL**: Never pass raw Rich objects directly to prompt_toolkit components.

- Convert Rich renderables to ANSI strings first:
```python
def rich_to_ansi(renderable, width=80):
    buffer = io.StringIO()
    console = Console(file=buffer, force_terminal=True, width=width)
    console.print(renderable)
    return buffer.getvalue()
```

- prompt_toolkit `FormattedText` must be a list of tuples:
```python
[('class:prompt-prefix', ' > '), ('style', 'text')]
```

- Use `ANSI()` wrapper for ANSI-encoded strings in prompt_toolkit:
```python
from prompt_toolkit.formatted_text import ANSI
return ANSI(rich_to_ansi(renderable, width))
```

## 4. Theme System Architecture (CRITICAL)

The theme system follows a **Core-API-UI** architecture. All theme operations must go through:

### Theme Data Flow

```
config/settings.json (source of truth)
    ↓
core/config_manager.py (get_customs())
    ↓
core/theme_engine.py (get_current_theme_colors())
    ↓
UI Components (dynamic fetching)
```

### Proper Theme Access

Always use `core.theme_engine` for theme operations:

```python
from core.theme_engine import get_current_theme_colors, get_current_theme

# In render loops - fetch EVERY frame
colors = get_current_theme_colors()
primary = colors.get("primary")      # #A9B7C6 (Darcula)
background = colors.get("background")  # #2B2B2B (Darcula)
success = colors.get("success")     # #6A8759 (Darcula)
```

### Legacy Patterns (DO NOT USE)

These patterns are deprecated - use `get_current_theme_colors()` instead:

```python
# WRONG - DO NOT USE:
from core.constants import get_colors_dict  # Deleted
from core.constants import THEME_COLORS       # Deleted
from commands.functions.theme.theme_logic import current_theme  # Broken
```

### Theme Colors

| Theme | Primary | Secondary | Background | Success |
|-------|---------|-----------|------------|---------|
| darcula | #A9B7C6 | #CC7832 | #2B2B2B | #6A8759 |
| matrix | #00FF41 | #003B00 | #000500 | #00FF41 |
| cyber | #FF007F | #00FFFF | #0f0913 | #00FF00 |
| classic | #888888 | #ffffff | #1c1c1c | #00FF41 |

## 5. Project Structure

```
E:\ProjectDev\cli\
├── app/                        # Entry points
│   ├── myworld.py             # Main CLI app
│   ├── taskmgr_standalone.py  # Task Manager subprocess
│   └── settings_standalone.py # Settings subprocess
│
├── api/                        # Public API layer
│   └── theme_api.py           # Theme operations API
│
├── commands/                   # Command handlers
│   ├── handles/               # Simple commands (help, clear, quit)
│   ├── functions/             # Complex command modules
│   │   ├── theme/
│   │   ├── sysinfo/
│   │   ├── system/
│   │   └── copy/
│   └── config/               # User settings (shortcuts, aliases)
│
├── config/                    # Configuration
│   └── settings.json         # Theme and window settings
│
├── core/                      # Core logic (SINGLE SOURCE OF TRUTH)
│   ├── constants.py           # Global constants (delegates to theme_engine)
│   ├── config_manager.py     # Configuration management
│   ├── theme_engine.py      # Theme engine (get_current_theme_colors)
│   └── logger.py              # Crash logging
│
├── services/monitors/         # System monitors
│   ├── base_monitor.py       # Base monitor class
│   ├── cpu_monitor.py       # CPU monitoring
│   ├── ram_monitor.py       # RAM monitoring
│   ├── gpu_monitor.py       # GPU monitoring
│   └── net_monitor.py       # Network monitoring
│
├── template/                   # Response templates
│   └── result_response.py    # BaseResponseTemplate
│
├── ui/                        # UI layer
│   ├── components/           # Reusable widgets
│   ├── layout/               # Layout builders
│   ├── modules/              # UI state (tabs, panels, tracker)
│   ├── screens/             # Screen containers
│   └── styles/              # Theme styles
│
└── run.bat                   # Launch script
```

## 6. Workflow Rules

1. **Environment**: Always use `.venv/Scripts/python.exe`
2. **Terminal**: Use Windows Terminal (`wt.exe`) for testing - required for TrueColor
3. **Logging**: All errors redirect to `logs/mw_crash.log`. Check this file before reporting issues
4. **Auto-Fix**: If `ModuleNotFoundError` occurs, automatically run `pip install`
5. **Relaunch**: If app detects non-Windows Terminal, it will auto-relaunch in wt.exe
6. **Atomic Reset**: On startup, window size is forced to 120x30, buffer cleared, cursor reset to (0,0)

## 7. Adding New Commands

To add a new command (e.g., `/mycommand`):

1. Create `commands/functions/mycommand/mycommand_logic.py` for business logic
2. Create `commands/functions/mycommand/mycommand_cmd.py` for command handler
3. Add handler to `commands/registry.py` dispatch function
4. Add completions to `ui/components/completer.py` DynamicCommandCompleter

## 8. Cursor Rules Summary

From `.cursorrules`:

- **Background color**: SHOULD be `#2B2B2B` for Darcula theme (not default terminal black `#0d1117`)
- **Logo**: Must be 2-blocks wide (`██`), use horizontal gradients, include mesh shadow (`░`)
- **Convert Rich to ANSI**: Before passing to prompt_toolkit
- **Force UTF-8**: stdout encoding for cross-shell compatibility
- **Check logs**: Always check `mw_crash.log` before asking user for feedback

## 9. Testing Guidelines

When adding tests:

```python
# Test file naming: tests/test_module_name.py
# Test function naming: test_function_name

import pytest

def test_theme_colors_darcula():
    from core.theme_engine import get_current_theme_colors
    colors = get_current_theme_colors()
    assert colors['primary'] == '#A9B7C6'
    assert colors['background'] == '#2B2B2B'

def test_config_manager():
    from core.config_manager import get_manager
    cfg = get_manager()
    assert cfg.get_customs() is not None
```

## 10. Common Development Tasks

| Task | Command |
|------|---------|
| Run app | `run.bat` |
| Syntax check single file | `python -m py_compile file.py` |
| Syntax check all Python | `python -m py_compile -r .` |
| List available themes | `python -c "from core.theme_engine import THEMES; print(list(THEMES.keys()))"` |
| Switch theme | `/theme --style darcula` in app |

---

*Generated: Project Architecture Guide (Updated: 2026-04-28)*