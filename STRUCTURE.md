# MYCOLOR CLI Project Structure

## 1. Directory Tree

```
E:\ProjectDev\cli\
├── app/                  # Application entry points
│   ├── myworld.py           # Main entry point
│   ├── taskmgr_standalone.py # Task Manager standalone
│   └── settings_standalone.py # Settings standalone
│
├── api/                  # API layer (public interface)
│   ├── __init__.py
│   └── theme_api.py        # Theme API for UI access
│
├── commands/              # Command handlers
│   ├── handles/           # Simple command handlers
│   │   ├── help.py
│   │   ├── clear.py
│   │   └── quit.py
│   ├── functions/         # Complex command modules
│   │   ├── copy/
│   │   │   ├── copy_cmd.py
│   │   │   └── copy_logic.py
│   │   ├── sysinfo/
│   │   │   ├── sysinfo_cmd.py
│   │   │   └── sysinfo_logic.py
│   │   ├── system/
│   │   │   ├── system_cmd.py
│   │   │   └── system_logic.py
│   │   └── theme/
│   │       ├── theme_cmd.py
│   │       └── theme_logic.py
│   └── config/
│       └── settings.json    # User settings (shortcuts, aliases)
│
├── core/                  # Core logic (business rules, data)
│   ├── constants.py        # Global constants
│   ├── logger.py           # Crash logger
│   ├── config_manager.py   # Configuration management
│   └── theme_engine.py     # Theme engine
│
├── services/              # Services layer (system data sources)
│   └── monitors/          # System monitors
│       ├── base_monitor.py # BaseMonitor class
│       ├── cpu_monitor.py  # CPU graph
│       ├── ram_monitor.py  # RAM graph
│       ├── gpu_monitor.py  # GPU graph
│       └── net_monitor.py  # Network graph
│
├── template/              # Response templates
│   ├── __init__.py
│   └── result_response.py
│
├── ui/                    # UI layer (presentation only)
│   ├── components/        # Reusable widgets
│   │   ├── completer.py   # Command auto-completion
│   │   ├── footer.py      # Footer bar
│   │   ├── input_area.py  # TextArea + key bindings
│   │   ├── logo.py        # ASCII logo
│   │   └── tips.py        # Tips display
│   │
│   ├── layout/            # Layout builders
│   │   ├── taskmgr_layout.py
│   │   └── settings_layout.py
│   │
│   ├── modules/           # UI state management (NO core logic here)
│   │   ├── constants.py  # UI constants only
│   │   ├── logger.py      # UI logger
│   │   ├── tabs/          # Task manager tabs
│   │   │   ├── base_tab.py
│   │   │   ├── performance_tab.py
│   │   │   ├── processes_tab.py
│   │   │   └── startup_tab.py
│   │   ├── panels/
│   │   │   └── detail_panel.py
│   │   └── tracker/
│   │       └── history_tracker.py
│   │
│   └── screens/           # Screen containers
│       ├── __init__.py
│       ├── intro_screen.py
│       ├── cmd_screen.py
│       ├── taskmgr_screen.py
│       └── settings_screen.py
│
├── utils/                 # Utilities
│   └── clipboard_manager.py
│
├── logs/                  # Log files
├── .venv/                 # Virtual environment
└── Root files             # run.bat, run_taskmgr.bat, run_settings.bat, AGENTS.md, etc.
```

## 2. Architecture: Core-API-UI

```
┌─────────────────────────────────────────────────────────────────┐
│                         UI LAYER                                 │
│  (ui/screens/, ui/components/, ui/layout/, ui/modules/)          │
│  - Presentation only                                             │
│  - Uses API to interact with Core                               │
│  - NO core logic (config, theme engine, etc.)                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│  (api/)                                                          │
│  - Public interface for UI                                       │
│  - Abstracts Core implementation                                  │
│  - Example: theme_api.get_available_themes()                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         CORE LAYER                               │
│  (core/, commands/)                                             │
│  - Business logic                                               │
│  - Data management                                               │
│  - Example: config_manager.py, theme_engine.py, logger.py       │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Component Responsibilities

### Entry Points (app/)
| File | Role |
|------|------|
| `myworld.py` | Main CLI app bootstrap, screen routing, Windows Terminal detection |
| `taskmgr_standalone.py` | Task Manager standalone subprocess |
| `settings_standalone.py` | Settings standalone subprocess |

### API Layer (api/)
| File | Role |
|------|------|
| `theme_api.py` | Public API for theme operations (get themes, set theme) |

### Core Layer (core/)
| File | Role |
|------|------|
| `config_manager.py` | Load/save configuration, manage settings.json |
| `theme_engine.py` | Theme color calculations, gradient generation |
| `logger.py` | Centralized crash logging |
| `constants.py` | Global constants |

### Commands (commands/)
| File | Role |
|------|------|
| `handles/help.py`, `clear.py`, `quit.py` | Simple command handlers |
| `functions/copy/*` | Copy command logic |
| `functions/sysinfo/*` | System info command |
| `functions/system/*` | System commands (taskmgr, etc.) |
| `functions/theme/*` | Theme command |
| `config/settings.json` | User preferences, shortcuts, aliases |

### Services Layer (services/)
| File | Role |
|------|------|
| `monitors/base_monitor.py` | Base monitor with graph rendering |
| `monitors/cpu_monitor.py` | CPU usage monitoring |
| `monitors/ram_monitor.py` | RAM usage monitoring |
| `monitors/gpu_monitor.py` | GPU monitoring (NVIDIA) |
| `monitors/net_monitor.py` | Network I/O monitoring |

### UI Layer (ui/)
| Directory | Role |
|-----------|------|
| `components/` | TextArea, completer, footer, logo, tips |
| `layout/` | Layout builders for taskmgr/settings |
| `screens/` | Screen containers (intro, cmd, taskmgr, settings) |
| `modules/` | UI state (tabs, panels, tracker) - NO core logic |

**IMPORTANT**: `ui/modules/` contains only UI-related modules. Core logic files (config_manager, theme_engine, logger, constants) must NOT be placed here. They belong in `core/`.

### Utilities (utils/)
| File | Role |
|------|------|
| `clipboard_manager.py` | Clipboard operations |

---

*Generated: Project Architecture Audit (Updated: 2026-04-27)*