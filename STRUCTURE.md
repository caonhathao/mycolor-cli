# MYCOLOR CLI Project Structure

## 1. Directory Tree

```
E:\ProjectDev\cli\
├── myworld.py                 # Redirects to app/myworld.py (deprecated, use run.bat)
├── config.json              # Theme and window settings (old, migrated to config/)
├── run.bat                 # Main launch script
├── run_taskmgr.bat         # Task Manager launch script
├── run_settings.bat       # Settings launch script
├── requirements.txt        # Dependencies
├── README.md              # Documentation
├── AGENTS.md             # Developer guide
│
├── app/                  # Application entry points
│   ├── myworld.py       # Main entry point
│   ├── taskmgr_standalone.py  # Task Manager UI
│   └── settings_standalone.py # Settings UI
│
├── config/              # Configuration files
│   └── settings.json  # Customizations, shortcuts, commands
│
├── logs/               # Log files
│   ├── mw_crash.log   # Main application crash reports
│   ├── settings_debug.log # Settings UI debug logs
│   ├── pulse.log     # Task Manager UI pulse logs
│   └── [other log files]
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
│   ├── taskmgr_layout.py # Task manager layout builder
│   └── settings_layout.py # Settings layout builder
│
├── modules/          # System monitoring modules
│   ├── __init__.py
│   ├── constants.py     # Configuration Gatekeeper - loads settings.json, provides centralized constants
│   ├── monitors/   # System monitors
│   │   ├── __init__.py
│   │   ├── base_monitor.py  # BaseMonitor class
│   │   ├── cpu_monitor.py  # CPU graph monitor
│   │   ├── ram_monitor.py  # RAM graph monitor
│   │   ├── gpu_monitor.py  # GPU graph monitor
│   │   └── net_monitor.py  # Network I/O monitor
│   ├── panels/
│   │   ├── __init__.py
│   │   └── detail_panel.py  # Detail panel for selected item
│   ├── tabs/       # Task manager tabs
│   │   ├── __init__.py
│   │   ├── base_tab.py      # BaseTab class
│   │   ├── performance_tab.py # CPU/RAM/GPU/Network graphs tab
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
│   ├── taskmgr_screen.py # Task manager interface
│   └── settings_screen.py # Settings interface
│
├── template/       # Response templates
│   ├── __init__.py
│   └── result_response.py # BaseResponseTemplate
│
└── .venv/        # Virtual environment
```

## 2. Component & File Responsibilities

### Entry Points (app/)
| File | Role |
|------|------|
| `myworld.py` | Main application bootstrap, screen routing, prompt_toolkit Application setup, Windows Terminal detection and relaunch |
| `taskmgr_standalone.py` | Standalone entry point for Task Manager UI |
| `settings_standalone.py` | Standalone entry point for Settings UI |

### Configuration (config/)
| File | Role |
|------|------|
| `settings.json` | Customizations, keyboard shortcuts, command aliases |

### Logs (logs/)
| File | Purpose |
|------|---------|
| `mw_crash.log` | Main application crash reports |
| `settings_debug.log` | Settings UI debug logs |
| `pulse.log` | Task Manager UI pulse logs |
| Other logs | Worker lifecycle, render confirm, UI data access |

### Components (UI Widgets)
Same as before - unchanged responsibility.

---

*Generated: Project Architecture Audit (Updated: 2026-04-25)*