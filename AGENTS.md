# AGENTS.md - MYCOLOR CLI Developer Guide

This document provides guidelines for AI agents working on the MYCOLOR CLI project.

## 1. Project Overview

MYCOLOR CLI is a Python-based Terminal User Interface (TUI) application that provides a vibrant, premium command-line experience with system monitoring capabilities.

- **Language**: Python 3.12+
- **Entry Point**: `myworld.py`
- **Tech Stack**: `prompt_toolkit` (UI), `rich` (styling), `psutil` (system metrics)
- **Platform**: Windows (primary), requires Windows Terminal for TrueColor support

## 2. Build, Lint, and Test Commands

### Running the Application

```cmd
run.bat
```

Or directly with the virtual environment:

```cmd
.venv\Scripts\python.exe myworld.py
```

### Linting and Type Checking

This project does not have a configured linter or type checker. If you add one, prefer:
- `ruff` for fast linting
- `mypy` for type checking

### Testing

**No test framework is currently configured.** There are no test files in the codebase.

To add testing:
```cmd
pip install pytest pytest-asyncio
pytest                    # Run all tests
pytest tests/              # Run tests in specific directory
pytest -v                 # Verbose output
pytest -k test_name       # Run specific test by name
```

## 3. Code Style Guidelines

### General Conventions

- **Line Length**: Keep lines under 120 characters when practical
- **Indentation**: 4 spaces (no tabs)
- **Encoding**: UTF-8 (use `sys.stdout.reconfigure(encoding='utf-8')` for cross-shell compatibility)
- **Line Endings**: LF (Unix-style) preferred; project uses Windows batch scripts

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `BaseMonitor`, `DynamicCommandCompleter` |
| Functions/Variables | snake_case | `get_input_text_area`, `handle_help_command` |
| Constants | UPPER_SNAKE_CASE | `HORIZONTAL = "─"` |
| Private methods | Leading underscore | `_generate_graph_text` |

### Imports

Order imports in the following groups (separated by blank lines):

1. Standard library (`os`, `sys`, `json`, `asyncio`)
2. Third-party libraries (`rich`, `prompt_toolkit`)
3. Custom modules (`functions.*`, `components.*`, `modules.*`)

```python
import os
import sys
import asyncio

from rich.console import Console
from rich.panel import Panel

from functions.theme.theme_logic import load_config
from components.input_area import get_input_text_area
```

### Types

The codebase does not currently use type hints extensively, but when adding new code:
- Use type hints for function signatures and return types
- Prefer `typing` module for complex types (`List`, `Dict`, `Optional`, `Union`)

```python
def process_data(data: List[float], max_val: Optional[float] = None) -> str:
    ...
```

### Error Handling

- Use try/except blocks with specific exception types when possible
- For critical operations that crash the app, catch and log to `mw_crash.log`
- Handle `PermissionError` by closing file handles before rewriting
- Use broad `except Exception` only when error type is truly unknown

```python
try:
    with open(config_path, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    # Use default config
    config = {}
except json.JSONDecodeError as e:
    log_to_buffer(f"[bold red]Config error: {e}[/bold red]")
```

### Rich and prompt_toolkit Integration

**CRITICAL**: Never pass raw Rich objects directly to prompt_toolkit components.

- Convert Rich renderables to ANSI strings first:
```python
from rich.console import Console
import io

def rich_to_ansi(renderable, width=80):
    console = Console(file=io.StringIO(), force_terminal=True, width=width)
    console.print(renderable)
    return console.file.getvalue()
```

- prompt_toolkit `FormattedText` must be a list of tuples:
```python
[('class:prompt-prefix', ' > '), ('style', 'text')]
```

### Visual Design

- **Background**: Always use `#0d1117` (not default terminal black)
- **Logo**: 2-block wide (`██`), use horizontal gradients (Cyan -> Purple -> Pink), include mesh shadow (`░`)
- **Terminal Size**: Default 120x30, use `shutil.get_terminal_size()` for dynamic calculations
- **Centering**: Calculate vertical padding dynamically using terminal size

## 4. Project Structure

```
myworld.py           # Entry point, main app loop
config.json          # Theme and window settings
run.bat              # Launch script
components/          # UI widgets (input_area, footer, logo, tips, completer)
screens/             # Screen logic (intro, cmd, taskmgr)
layout/              # Layout definitions (VSplit/HSplit containers)
functions/          # Command handlers (theme, sysinfo, system, help, clear, quit)
modules/monitors/    # System monitors (cpu, ram, gpu, net)
utils/               # Utilities (clipboard_manager)
template/            # Response templates
```

## 5. Workflow Rules

1. **Environment**: Always use `.venv/Scripts/python.exe`
2. **Terminal**: Use Windows Terminal (`wt.exe`) for testing - required for TrueColor
3. **Logging**: All errors redirect to `mw_crash.log`. Check this file before reporting issues
4. **Auto-Fix**: If `ModuleNotFoundError` occurs, automatically run `pip install`
5. **Relaunch**: If app detects non-Windows Terminal, it will auto-relaunch in wt.exe
6. **Atomic Reset**: On startup, window size is forced to 120x30, buffer cleared, cursor reset to (0,0)

## 6. Cursor Rules Summary

From `.cursorrules`:
- Background color MUST be `#0d1117`
- Logo must be 2-blocks wide with horizontal gradients
- Convert Rich to ANSI before passing to prompt_toolkit
- Force UTF-8 stdout encoding
- Check `mw_crash.log` before asking user for feedback

## 7. Adding New Commands

To add a new command (e.g., `/mycommand`):

1. Create `functions/mycommand/mycommand_logic.py` for business logic
2. Create `functions/mycommand/mycommand_cmd.py` for command handler
3. Add handler to `input_area.py` accept_input function
4. Add completions to `components/completer.py` DynamicCommandCompleter
5. Update `functions/__init__.py` if needed
