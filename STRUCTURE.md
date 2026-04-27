# MYCOLOR CLI Project Structure

## 1. Directory Tree

```
E:\ProjectDev\cli\
├── app/                     # Application entry points
│   ├── myworld.py            # Main CLI app
│   ├── taskmgr_standalone.py # Task Manager standalone subprocess
│   └── settings_standalone.py # Settings standalone subprocess
│
├── api/                     # PUBLIC API LAYER (Core-API-UI)
│   ├── __init__.py
│   ├── theme_api.py          # Theme operations (get/set themes)
│   └── system_api.py         # System data bridge to monitors
│
├── commands/                 # Command handlers
│   ├── registry.py           # CENTRAL DISPATCHER (all /commands route here)
│   ├── handles/            # Simple handlers (help, clear, quit)
│   │   ├── help.py
│   │   ├── clear.py
│   │   └── quit.py
│   └── functions/           # Complex command modules
│       ├── copy/
│       │   ├── copy_cmd.py
│       │   └── copy_logic.py
│       ├── sysinfo/
│       │   ├── sysinfo_cmd.py
│       │   └── sysinfo_logic.py
│       ├── system/
│       │   ├── system_cmd.py
│       │   └── system_logic.py
│       └── theme/
│           ├── theme_cmd.py
│           └── theme_logic.py   # Delegates to core/theme_engine.py
│
├── config/                   # SINGLE SOURCE OF TRUTH
│   └── settings.json        # Theme, shortcuts, aliases, customs
│
├── core/                    # SINGLE SOURCE OF TRUTH (Core-API-UI)
│   ├── config_manager.py      # Load/save settings.json
│   ├── theme_engine.py      # get_current_theme_colors() at RENDER TIME
│   ├── logger.py           # Crash logging to logs/
│   └── constants.py        # Global constants (delegates to theme_engine)
│
├── services/               # System data sources
│   └── monitors/           # System monitors
���       ├── base_monitor.py  # BaseMonitor class
│       ├── cpu_monitor.py # CPU graph
│       ├── ram_monitor.py # RAM graph
│       ├── gpu_monitor.py # GPU graph
│       └── net_monitor.py # Network graph
│
├── template/                # Response templates
│   └── result_response.py  # BaseResponseTemplate
│
├── ui/                    # UI LAYER (presentation only)
│   ├── components/         # Reusable widgets
│   │   ├── completer.py   # DynamicCommandCompleter
│   │   ├── footer.py
│   │   ├── input_area.py
│   │   ├── logo.py
│   │   └── tips.py
│   ├── layout/            # Layout builders
│   │   ├── taskmgr_layout.py
│   │   └── settings_layout.py
│   ├── modules/           # UI STATE ONLY (NO core logic)
│   │   ├── tabs/         # Task manager tabs
│   │   │   ├── base_tab.py
│   │   │   ├── performance_tab.py
│   │   │   ├── processes_tab.py
│   │   │   └── startup_tab.py
│   │   ├── panels/       # Detail panels
│   │   └── tracker/      # History tracker
│   ├── screens/          # Screen containers
│   │   ├── intro_screen.py
│   │   ├── cmd_screen.py
│   │   ├── taskmgr_screen.py
│   │   └── settings_screen.py
│   └── styles/           # Theme styles
│       └── theme_styles.py
│
├── utils/                  # Utilities
│   └── clipboard_manager.py
│
├── logs/                   # Log files (logs/mw-crash-debug.log)
├── .venv/                  # Virtual environment
└── run.bat                 # Launch script
```

## 2. Architecture: Core-API-UI

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI LAYER                                 │
│  (ui/screens/, ui/components/, ui/layout/, ui/modules/)          │
│                                                                  │
│  - Presentation only                                              │
│  - Uses API to interact with Core                                 │
│  - NO core logic (config, theme engine, logger here)             │
│  - Calls get_current_theme_colors() at RENDER TIME               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  (api/theme_api.py, api/system_api.py)                           │
│                                                                  │
│  - Public interface for UI                                       │
│  - Abstracts Core implementation                                  │
│  - Example: theme_api.get_available_themes()                     │
│  - Example: system_api.get_system_bridge()                         │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CORE LAYER                               │
│  (core/, commands/, config/, services/)                          │
│                                                                  │
│  - Business logic and data management                            │
│  - config/settings.json = SINGLE SOURCE OF TRUTH               │
│  - theme_engine.get_current_theme_colors() = DYNAMIC at render     │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Component Responsibilities

### Entry Points (app/)
| File | Role |
|------|------|
| `myworld.py` | Main CLI app, screen routing, Windows Terminal detection |
| `taskmgr_standalone.py` | Task Manager subprocess |
| `settings_standalone.py` | Settings subprocess |

### API Layer (api/)
| File | Role |
|------|------|
| `theme_api.py` | Public API for theme operations |
| `system_api.py` | Bridge to services/monitors |

### Core Layer (core/)
| File | Role |
|------|------|
| `config_manager.py` | Load/save configuration, singleton pattern |
| `theme_engine.py` | **DYNAMIC** theme colors at render time |
| `logger.py` | Crash logging |
| `constants.py` | Global constants (delegates to theme_engine) |

### Commands (commands/)
| File | Role |
|------|------|
| `registry.py` | **CENTRAL DISPATCHER** - all /commands route here |
| `handles/help.py`, `clear.py`, `quit.py` | Simple handlers |
| `functions/copy/*` | Copy command logic |
| `functions/sysinfo/*` | System info command |
| `functions/system/*` | System commands (taskmgr, etc.) |
| `functions/theme/*` | Theme command |

### Services Layer (services/)
| File | Role |
|------|------|
| `monitors/base_monitor.py` | Base monitor with graph rendering |
| `monitors/cpu_monitor.py` | CPU usage |
| `monitors/ram_monitor.py` | RAM usage |
| `monitors/gpu_monitor.py` | GPU monitoring |
| `monitors/net_monitor.py` | Network I/O |

### UI Layer (ui/)
| Directory | Role |
|-----------|------|
| `components/` | TextArea, completer, footer, logo, tips |
| `layout/` | Layout builders |
| `screens/` | Screen containers |
| `modules/` | **UI STATE ONLY** - tabs, panels, tracker |

**CRITICAL**: `ui/modules/` contains only UI-related modules. Core logic files belong in `core/`:
- ❌ DO NOT put config_manager.py, theme_engine.py, logger.py here
- ✅ Only ui/state modules (tabs, panels, tracker)

### Utilities (utils/)
| File | Role |
|------|------|
| `clipboard_manager.py` | Clipboard operations |

---

## 4. Key Patterns

### Theme Access (DYNAMIC)
```python
# UI fetches colors EVERY frame in render loops
from core.theme_engine import get_current_theme_colors

def render(self):
    colors = get_current_theme_colors()  # DYNAMIC - not cached
    primary = colors.get("primary")
```

### Command Dispatch
```python
# commands/registry.py - CENTRAL DISPATCHER
def dispatch(command_text):
    if command_text.startswith("/theme"):
        return handle_theme_command(command_text, ...)
    elif command_text.startswith("/sysinfo"):
        return handle_sysinfo_command(command_text, ...)
    # ...
```

### Data Bridge
```python
# api/system_api.py - Bridge to monitors
from services.monitors.cpu_monitor import CPUMonitor

def get_cpu_monitor(self):
    return CPUMonitor()
```

---

*Generated: Project Structure (Updated: 2026-04-28)*