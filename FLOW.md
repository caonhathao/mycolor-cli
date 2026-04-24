# MYCOLOR CLI Code Flow

This document explains the execution flow from startup through command execution.

---

## 1. Application Lifecycle

### 1.1 Entry Point Sequence (Main Process)

```
app/myworld.py (or run.bat)
  ├── 1. early_window_resize()      # Set terminal to 120x30
  ├── 2. ensure_config_exists()   # Create config.json if missing
  ├── 3. load_config()          # Load theme/window settings
  ├── 4. main_app()             # Async entry point
       ├── Check WT_SESSION      # Detect Windows Terminal
       ├── Relaunch in wt.exe   # If not in WT, relaunch
       ├── Create Application   # prompt_toolkit Application
       ├── Initialize Screens   # intro/cmd containers
       ├── Create KeyBindings
       ├── Set Layout + Style
       └── application.run_async()
```

### 1.1.1 Entry Point Sequence (Task Manager)

```
app/taskmgr_standalone.py (or run_taskmgr.bat)
  ├── 1. early_window_resize()      # Set terminal to 120x30
  ├── 2. ensure_config_exists()   # Create config.json if missing
  ├── 3. load_config()          # Load theme/window settings
  ├── 4. main_taskmgr()         # Async entry point
       ├── Create Application # prompt_toolkit Application
       ├── Create KeyBindings  # q/ESC to quit, arrows for tab navigation
       ├── get_taskmgr_layout()  # Build layout via TaskManagerInterface
       ├── Attach unique app_state to Application
       ├── Create background task for update_loop()
       └── application.run_async()
```

### 1.1.2 Entry Point Sequence (Settings)

```
app/settings_standalone.py (or run_settings.bat)
  ├── 1. early_window_resize()      # Set window to 100x35
  ├── 2. ensure_config_exists()   # Create config.json if missing
  ├── 3. load_config()          # Load theme/window settings
  ├── 4. main_settings()       # Async entry point
       ├── Create Application # prompt_toolkit Application
       ├── Create KeyBindings  # Tab nav, edit mode, Alt+S save
       ├── get_settings_layout() # Build layout via SettingsInterface
       ├── Attach unique app_state to Application
       └── application.run_async()
```

### 1.2 Screen Routing (Main Process)

```
myworld.py:141-176
├── app_state["current_screen"] = "intro" | "cmd" | "taskmgr"
├── get_root_container()          # DynamicContainer callback
│   ├── "intro" → intro_container
│   ├── "cmd"   → cmd_container
│   └── "taskmgr" → taskmgr_container (DEPRECATED - use standalone instead)
└── application.layout = Layout(root_container, focused_element)
```

### 1.3 Intro → Cmd Transition

```
intro_screen.py (on_input_accept)
  └── On first Enter key:
      ├── app_state["current_screen"] = "cmd"
      ├── application.renderer.erase()
      └── application.invalidate()
```

---

## 2. Command Execution Flow

### 2.1 Input to Output Pipeline

```
┌──────────────────────────────────────────────────────────────────────┐
│ INPUT PHASE                                                      │
├──────────────────────────────────────────────────────────────────────┤
│ 1. User types command in TextArea                                  │
│ 2. User presses Enter                                            │
│ 3. accept_input(buff) is invoked                                 │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ROUTING PHASE                                                     │
├─────��────────────────────────────────────────────────────────────────┤
│ 4. accept_input() routes by prefix                                │
│    ├── "/theme" → handle_theme_command()                          │
│    ├── "/sysinfo" → handle_sysinfo_command()                       │
│    ├── "/system" → handle_system_command()                        │
│    ├── "/copy" → handle_copy_command()                           │
│    ├── "/help" → handle_help_command()                          │
│    ├── "/clear" → handle_clear_command()                       │
│    ├── "/quit" → application.exit()                           │
│    ├── Shell builtins (pwd, ls, cd, cls)                       │
│    └── Default → shell subprocess                             │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ EXECUTION PHASE                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ 5. Handler executes logic                                      │
│    └── May call run_system_command() for subprocess            │
│        ├── Create asyncio subprocess                           │
│        ├── Stream stdout/stderr line-by-line                  │
│        └── Log each line via log_to_buffer()                 │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ OUTPUT PHASE                                                      │
├──────────────────────────────────────────────────────────────────────┤
│ 6. log_to_buffer(renderable, save_to_history=True)              │
│    ├── rich_to_ansi() via _ANSI_CONSOLE                       │
│    ├── Insert ANSI string to output_buffer                     │
│    ├── Append plain text to history_tracker                 │
│    └── Invalidate application for redraw                    │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ RENDER PHASE                                                      │
├──────────────────────���─��─────────────────────────────────────────────┤
│ 7. FormattedTextControl.get_formatted_content()                  │
│    ├── Convert ANSI to FormattedText                              │
│    └── Return to prompt_toolkit renderer                      │
│                                                                  │
│ 8. Output Window renders content                                │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Key Binding Flow

```
Key Press Event
    │
    ├── KeyBindings match (in order)
    │   ├── Input Area Bindings (input_area.py)
    │   │   ├── Ctrl+C / Ctrl+Q → quit_app()
    │   │   ├── Alt+Q → alt_q_quit()
    │   │   ├── Ctrl+L → clear_terminal()
    │   │   ├── Alt+C → clear input buffer
    │   │   ├── Ctrl+V → paste from clipboard
    │   │   ├── Shift+Up → history_backward()
    │   │   └── Shift+Down → history_forward()
    │   │
    │   └── Cmd Screen Bindings (cmd_screen.py)
    │       ├── Tab → disabled (pass)
    │       ├── PageUp → cursor_up(10)
    │       ├── PageDown → cursor_down(10)
    │       ├── ScrollUp → cursor_up(5)
    │       └── ScrollDown → cursor_down(5)
    │
    └── Event propagates to handler
```

### 2.3 Notification Flow

```
Command Handler (e.g., copy_cmd.py)
    │
    ├── Notification triggered
    │   └── notification_trigger(message, is_success=True)
    │
    trigger_notification():
    │   ├── Build Rich markup box
    │   ├── Convert to ANSI
    │   ├── state.notification_message = plain_text
    │   ├── state.show_notification = True
    │   └── app.create_background_task(hide_after_5s)
    │
    hide_notification() (after 5 seconds):
    │   ├── state.show_notification = False
    │   └── app.invalidate()
    │
    FloatContainer renders via ConditionalContainer
```

---

## 3. Task Manager Flow (Standalone Subprocess)

### 3.1 Launch Flow

```
/system --taskmgr (command in main app)
    │
    ├── handle_system_command() parses --taskmgr flag
    │
    ├── Subprocess launch via run_taskmgr.bat
    │   └── .venv\Scripts\python.exe taskmgr_standalone.py
    │
    └── Independent process with unique app_state
```

### 3.2 Worker Lifecycle (Background Threads)

```
PerformanceTab.on_activate()
    │
    ├── Clear stop events
    │   ├── _stop_event_cpu_ram.clear()
    │   ├── _stop_event_gpu.clear()
    │   └── _stop_event_net.clear()
    │
    ├── Spawn worker threads
    │   ├── worker_cpu_ram()  → Polls CPU + RAM every 0.5s
    │   ├── worker_gpu()     → Polls GPU every 1.0s
    │   └── worker_net()     → Polls Network every 0.5s
    │
    └── _log_lifecycle("THREAD STARTED")
```

```
PerformanceTab.on_deactivate()
    │
    ├── Set stop events
    │   ├── _stop_event_cpu_ram.set()
    │   ├── _stop_event_gpu.set()
    │   └── _stop_event_net.set()
    │
    ├── Join threads
    │   └── thread.join(timeout)
    │
    └── _log_lifecycle("THREAD EXITED")
```

### 3.3 Sampling Pipeline (No-Cache)

```
REFRESH_INTERVAL = 0.5s
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 1: FETCH                                                     │
├──────────────────────────────────────────────────────────────────────┤
│ Monitor.update()                                                 │
│     ├── psutil.cpu_percent() / psutil.virtual_memory()              │
│     ├── nvidia-ml-py (if GPU available)                          │
│     ├── psutil.net_io_counters()                                 │
│     └── Append value to history[] deque                          │
└──────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 2: RENDER                                                     │
├──────────────────────────────────────────────────────────────────────┤
│ Monitor.render(width, height)                                    │
│     ├── _get_graph_text() - Generate ASCII graph                  │
│     ├── Render Panel via Rich.Console                             │
│     └── self.cached_frame = ANSI string                           │
└──────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────���───────────────────────────┐
│ STEP 3: UI ACCESS (REGENERATE EVERY TIME)                        │
├──────────────────────────────────────────────────────────────────────┤
│ PerformanceTab.render()                                          │
│     ├── Call monitor.get_cached_frame_safe()                   │
│     │   └── Returns self.cached_frame (pre-rendered)            │
│     │                                                          │
│     └── UI calls get_cached_formatted()                        │
│         └── PT_ANSI(self.cached_frame)  ← REGENERATED EVERY CALL│
└──────────────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────────────┐
│ STEP 4: INVALIDATE                                                │
├──────────────────────────────────────────────────────────────────────┤
│ Background thread signals UI for redraw                         │
│     ├── _try_invalidate()                                        │
│     ├── Check current_screen == "taskmgr"                       │
│     ├── Get app_id = id(app)                                     │
│     ├── Log to render_confirm.log                                │
│     └── app.invalidate() → Force frame redraw                   │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.4 Process Tab Rendering

```
ProcessesTab.render():
    │
    ├── Check hash cache (skip if unchanged)
    │
    ├── Fetch processes via psutil
    │   └── process_batch = [p for p in psutil.process_iter(...)]
    │
    ├── Filter by config (hide_system_processes)
    │
    ├── Sort by PID ascending
    │
    ├── Render static strings with f-strings
    │
    └── Cache rendered ANSI string
```

### 3.5 Graph Monitors

```
BaseMonitor (modules/monitors/base_monitor.py):
    ├── start()           # Begin collection
    ├── collect()        # Collect metric
    ├── get_graph()      # Generate ASCII graph
    ├── stop()           # End collection
    ├── get_cached_formatted() → PT_ANSI regenerated every call

CPU/RAM/GPU/NetMonitor inherit BaseMonitor:
    ├── CPU: psutil.cpu_percent()
    ├── RAM: psutil.virtual_memory()
    ├── GPU: nvidia-ml-py (if available)
    └── Net: psutil.net_io_counters()
```

---

## 4. Data Flow Diagrams

### 4.1 Theme System

```
load_config()
    │
    ├── Read config.json
    │
    get_current_theme_colors()
    │   ├── Access current_theme dict
    │   └── Return color hex values
    │
    get_app_style()
    │   ├── Convert to prompt_toolkit PTStyle
    │   └── Apply via application.style
    │
    rich_to_ansi()
    │   └── Uses _ANSI_CONSOLE for rendering
```

### 4.2 History Tracker

```
accept_input() called
    │
    ├── get_history_tracker().start_new_entry(command)
    │
    ├── log_to_buffer() for each output
    │   └── get_history_tracker().append_result(text)
    │
    └── buff.history.append_string(command)
```

### 4.3 Screen State Transitions

```
┌─────────────────────────────────────────────────────────┐
│                    STATE MACHINE                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    ┌──────┐   Enter    ┌──────┐   /quit   ┌────────┐  │
│    │intro │ ────────→  │ cmd  │ ───────→   │ exit   │  │
│    └──────┘            └──────┘            └────────┘  │
│                           │                         ▼  │
│                           │    /system --taskmgr        │  │
│                           └────────────────────────→  ┌──────┐
│                                                    │taskmgr│
│                                                    │(subprocess)│
│                                                    └──────┘
└─────────────────────────────────────────────────────────┘
```

---

## 5. Component Relationships

### 5.1 Dependency Graph

```
myworld.py (Entry)
    │
    ├── functions/theme/theme_logic.py
    │   └── config.json
    │
    ├── components/
    │   ├── input_area.py
    │   │   ├── completer.py (DynamicCommandCompleter)
    │   │   ├── key bindings
    │   │   └── log_to_buffer()
    │   ├── logo.py
    │   ├── footer.py
    │   └── tips.py
    │
    ├── screens/
    │   ├── intro_screen.py
    │   │   └── logo.py + tips.py + input_area.py
    │   ├── cmd_screen.py
    │   │   ├── output_buffer (TextArea)
    │   │   ├── input_area.py
    │   │   └── notification_state
    │   └── taskmgr_screen.py (DEPRECATED - use standalone)
    │       └── layout/taskmgr_layout.py
    │       └── modules/ (tabs, monitors, panels)
    │
    ├── modules/tracker/
    │   └── history_tracker.py
    │
    └── functions/ (command handlers)
        ├── theme/theme_cmd.py → theme_logic.py
        ├── sysinfo/sysinfo_cmd.py → sysinfo_logic.py
        ├── system/system_cmd.py → system_logic.py
        └── copy/copy_cmd.py → copy_logic.py

taskmgr_standalone.py (Independent Subprocess Entry)
    │
    ├── functions/theme/theme_logic.py
    │   └── config.json
    │
    ├── layout/taskmgr_layout.py
    │   └── get_taskmgr_layout()
    │
    ├── screens/taskmgr_screen.py
    │   └── TaskManagerInterface
    │
    └── modules/tabs/performance_tab.py
        └── Worker threads (CPU/RAM/GPU/Net monitors)
```

### 5.2 Singleton Pattern

The following use singleton pattern:

| Singleton | Accessor | Location |
|-----------|---------|----------|
| `HistoryTracker` | `get_history_tracker()` | modules/tracker/history_tracker.py |
| Theme colors | `get_current_theme_colors()` | functions/theme/theme_logic.py |
| Config | `load_config()` / `_config` | functions/theme/theme_logic.py |
| App style | `get_app_style()` | functions/theme/theme_logic.py |
| Notification trigger | `get_notification_trigger()` | screens/cmd_screen.py |
| Notification clearer | `get_notification_clearer()` | screens/cmd_screen.py |

### 5.3 Unique State Isolation

| Process | app_state Keys | Isolation |
|---------|----------------|-----------|
| `myworld.py` | `current_screen`, `app_instance` | Shared between main screens |
| `taskmgr_standalone.py` | `current_screen`, `app_instance`, `taskmgr_instance` | Unique per subprocess |

---

## 6. Diagnostic Log Flow

### 6.1 Log File Generation

```
Application startup
    │
    ├── mw_crash.log        → Critical crashes (main entry)
    ├── crash_debug.log     → Runtime debug info
    │
    └── Task Manager subprocess
        ├── worker_lifecycle.log    → Worker thread events
        ├── render_confirm.log      → Render/invalidation signals
        └── ui_data_access.log   → UI data access patterns
```

### 6.2 Log Entry Examples

```python
# worker_lifecycle.log
[1234567.890] TID=1234 CPU_RAM: THREAD STARTED
[1234567.890] TID=1234 CPU_RAM: PULSE: event_set=False
[1234567.890] TID=1234 CPU_RAM: FETCHED: CPU=45.3 | hist_len=45
[1234568.390] TID=1234 CPU_RAM: THREAD EXITED (loop ended)

# render_confirm.log
[1234567.890] RENDER_CHECK: _has_update=True, app_id=140000, screen=taskmgr, tab=0
[1234567.890] INVALIDATE: signaling App 140000 (matches parent.app=True)
```

---

*Generated: Flow Analysis (Updated: 2026-04-23)*