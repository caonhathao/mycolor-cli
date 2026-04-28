# MYCOLOR CLI Code Flow

Dynamic operations documentation for the Core-API-UI architecture.

---

## 1. Theme Update Flow (DYNAMIC at Render Time)

Theme colors are fetched **dynamically** every frame - no caching.

```
┌──────────────────────────────────────────────────────────────────────┐
│ UI LAYER: settings_screen.py / taskmgr_screen.py                 │
├──────────────────────────────────────────────────────────────────────┤
│ def render():                                                 │
│     colors = get_current_theme_colors()  ← FETCH EVERY FRAME   │
│     primary = colors.get("primary")       # #A9B7C6 (Darcula)│
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ CORE LAYER: core/theme_engine.py                                  │
├──────────────────────────────────────────────────────────────────────┤
│ def get_current_theme_colors():                                  │
│     config = get_manager()                    # Singleton                 │
│     theme = config.get_customs().get("theme")  # "darcula"          │
│     return THEMES[theme]                  # HEX colors dict       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ CORE LAYER: core/config_manager.py                               │
├──────────────────────────────────────────────────────────────────────┤
│ def get_customs():                                             │
│     return self._settings.get("customs", {})                   │
│                                                            │
│ config/settings.json  ← SINGLE SOURCE OF TRUTH                │
│     "customs": { "theme": "darcula" }                         │
└──────────────────────────────────────────────────────────────────────┘
```

### Theme API Flow

```
settings_screen.py:confirm_popup()
       │
       ▼
api/theme_api.set_theme("matrix")
       │
       ▼
core/config_manager.update_theme("matrix")
       │
       ▼
core/theme_engine.apply_colors("matrix")
       │
       ▼
application.style = get_app_style()
```

---

## 2. Global Notification Flow

The Global Notification Service is rendered in any screen's FloatContainer via `get_notification_float()`.

```
┌──────────────────────────────────────────────────────────────────────┐
│ TRIGGER SOURCES: API/Cmd/Settings                                 │
├──────────────────────────────────────────────────────────────────────┤
│ api/theme_api.py:set_theme()                                      │
│ commands/functions/*:handle_*_command()                           │
│ ui/modules/tabs/settings/general_tab.py:confirm_popup()           │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ GLOBAL SERVICE: ui/layout/notification_layout.py                  │
├──────────────────────────────────────────────────────────────────────┤
│ trigger = get_notification_trigger()                              │
│ trigger("Operation successful!", is_success=True)                 │
│     │                                                            │
│     ▼                                                            │
│ notification_layout.trigger_notification()                        │
│     │                                                            │
│     ▼                                                            │
│ Global NotificationState → show_notification = True              │
│ message = "Operation successful!"                                │
│ is_success = True                                                │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│ RENDER: Any screen's FloatContainer                              │
├──────────────────────────────────────────────────────────────────────┤
│ get_notification_float()                                          │
│     │                                                            │
│     ▼                                                            │
│ Condition(lambda: show_notification and bool(message.strip()))    │
│     │                                                            │
│     ▼                                                            │
│ Green box (5s) for success / Red box (5s) for error              │
│ Auto-hide after timeout                                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Settings Navigation & Theme Application Flow

### Settings Navigation Flow

```
SettingsInterface (settings_screen.py - State Container)
       │
       ▼
active_tab.handle_input()  # general_tab / shortcuts_tab / commands_tab
       │
       ▼
Update parent.popup_options  # Set popup state
       │
       ▼
app.invalidate()  # Trigger re-render
       │
       ▼
Display Popup (confirmation dialog)
       │
       ▼
confirm_popup() → Write to settings.json → Trigger Global Notification
```

### Theme Application Flow (Delayed Apply)

```
User selects theme in general_tab.py
       │
       ▼
Write to settings.json via config_manager
       │
       ▼
Trigger Global Notification: "Theme will apply after restart"
       │
       ▼
UI remains same (current theme still active)
       │
       ▼
User restarts app → early_window_resize() → load settings.json
       │
       ▼
New theme colors applied at render time via get_current_theme_colors()
```

**Note**: Theme changes are NOT applied immediately. Users must restart the app to see changes.

---

## 4. Command Dispatch Flow

All commands route through `commands/registry.py`.

```
┌──────────────────────────────────────────────────────────────────────┐
│ INPUT: User types "/theme --style darcula" in input_area.py        │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ ROUTING: input_area.py → accept_input()                           │
├──────────────────────────────────────────────────────────────────────┤
│ def accept_input(buff):                                        │
│     command_text = buff.text                                    │
│     dispatch_command(command_text, ...)  # → registry.py       │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ DISPATCHER: commands/registry.py                                │
├──────────────────────────────────────────────────────────────────────┤
│ def dispatch_command(command_text, ...):                         │
│     if command_text.startswith("/theme"):                     │
│         return handle_theme_command(...)                       │
│     elif command_text.startswith("/sysinfo"):                │
│         return handle_sysinfo_command(...)                     │
│     elif command_text.startswith("/system"):                  │
│         return handle_system_command(...)                     │
│     elif command_text.startswith("/copy"):                     │
│         return handle_copy_command(...)                       │
│     elif command_text.startswith("/help"):                     │
│         return handle_help_command(...)                         │
│     elif command_text.startswith("/clear"):                   │
│         return handle_clear_command(...)                         │
│     elif command_text.startswith("/quit"):                    │
│         return handle_quit_command(...)                       │
│     else:                                                     │
│         return handle_shell_command(...)  # subprocess        │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ HANDLER: commands/functions/theme/theme_cmd.py                  │
├──────────────────────────────────────────────────────────────────────┤
│ def handle_theme_command(command_text, ...):                   │
│     colors = get_current_theme_colors()  # Use dynamic colors  │
│     success_color = colors.get("success")                     │
│     ...                                                       │
│     log_func(base_output)                                      │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ OUTPUT: template/result_response.py → BaseResponseTemplate    │
├──────────────────────────────────────────────────────────────────────┤
│ def log_to_buffer(renderable, save_to_history=True):             │
│     ansi = rich_to_ansi(renderable)                            ���
│     output_buffer.append(ansi)                                │
│     invalidate_app()                                          │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ RENDER: cmd_screen.py → FormattedTextControl                    │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow (Monitors → API → UI)

```
┌──────────────────────────────────────────────────────────────────────┐
│ SERVICES LAYER: services/monitors/*_monitor.py               │
├──────────────────────────────────────────────────────────────────────┤
│ CPUMonitor:                                                   │
│     psutil.cpu_percent() → history deque                      │
│     render() → ASCII graph → ANSI string                     │
│                                                            │
│ RAMMonitor, GPUMonitor, NetMonitor                           │
│     (same pattern)                                           │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────���────┐
│ API LAYER: api/system_api.py                                 │
├──────────────────────────────────────────────────────────────────────┤
│ class SystemDataBridge:                                       │
│     get_cpu_monitor() → CPUMonitor                         │
│     get_ram_monitor() → RAMMonitor                         │
│     ...                                                     │
│                                                            │
│ def get_system_bridge():  # Singleton                       │
│     return _bridge                                │
└──────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│ UI LAYER: ui/modules/tabs/performance_tab.py                │
├──────────────────────────────────────────────────────────────────────┤
│ PerformanceTab.render():                                   │
│     bridge = get_system_bridge()                           │
│     cpu = bridge.get_cpu_monitor()                         │
│     frame = cpu.get_cached_formatted()                      │
│     return PT_ANSI(frame)                                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 6. Application Lifecycle

### Entry Point (Main Process)

```
app/myworld.py
  ├── early_window_resize()  # 120x30
  ├── ensure_config_exists()
  ├── main_app()
       ├── Detect Windows Terminal
       ├── Create Application
       ├── Initialize Screens
       ├── Set Layout
       └── application.run_async()
```

### Task Manager Subprocess

```
app/taskmgr_standalone.py
  ├── early_window_resize()  # 120x30
  ├── main_taskmgr()
       ├── Create Application
       ├── Create KeyBindings
       ├── get_taskmgr_layout()
       └── application.run_async()
```

---

## 7. Screen State Transitions

```
┌─────────────────────────────────────────────────────────┐
│ intro ──Enter──▶ cmd ──/quit──▶ exit                  │
│                    │                                   │
│                    └──/system --taskmgr──▶ taskmgr    │
│                      (subprocess)                      │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Key Singletons

| Singleton | Accessor | Location |
|-----------|---------|----------|
| `ConfigManager` | `get_manager()` | core/config_manager.py |
| `ThemeEngine` | `get_theme_engine()` | core/theme_engine.py |
| Theme colors | `get_current_theme_colors()` | core/theme_engine.py |
| `SystemDataBridge` | `get_system_bridge()` | api/system_api.py |
| `HistoryTracker` | `get_history_tracker()` | ui/modules/tracker/history_tracker.py |

---

## 9. Log Files

All logs managed by `core/logger.py` in `logs/` directory.

| Log | Purpose |
|-----|---------|
| `mw-crash-debug.log` | App crashes |
| `taskmgr-ui-debug.log` | Task Manager UI |
| `performance-*-debug.log` | Worker threads |

---

*Generated: Flow Documentation (Updated: 2026-04-29)*