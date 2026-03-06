# MYCOLOR CLI | System Monitor

> [!NOTE]
> *Elevating the terminal experience from the mundane to the magnificent.*

> [!NOTE]
> *This project uses only an AI agent to build. No human code.*

**MYCOLOR CLI** is a vibrant, premium Terminal User Interface (TUI) application that transforms the standard system monitor into a visually stunning command-line experience. With support for multiple color themes and real-time system metrics, it brings a "new coat of paint" to the command line.

---

## ✨ Key Features

### 📊 Processes Tab
- **Real-time Process Monitoring**: View all running processes with PID, Name, User, Threads, Handles, CPU%, and MEM%
- **Persistent CPU Deltas**: Advanced caching system using `psutil.Process` object persistence enables accurate CPU percentage calculation across fetch cycles
- **Responsive Vertical Scaling**: Automatically adapts to terminal height with proper scrolling
- **Access Denied Handling**: Gracefully handles high-privilege processes without breaking CPU tracking

### 📈 Performance Tab
- **2x2 Monitor Grid**: Four real-time system monitors in an optimized layout
  - **CPU Monitor**: Tracks overall CPU usage with history graph
  - **RAM Monitor**: Displays memory utilization percentage
  - **GPU Monitor**: NVIDIA GPU utilization (via WMI) or GPUtil
  - **Network Monitor**: Auto-scaling upload/download speed visualization
- **8-Core Visualization**: High-resolution history graphs using block characters (▂▃▄▅▆▇█)
- **Background Updates**: Non-blocking data fetching ensures smooth input responsiveness

### 🎨 Theme System
Four distinct themes with persistent configuration:
| Theme | Primary Color | Description |
| :--- | :--- | :--- |
| **Classic** | Grey (#888888) | Metallic silver with clean aesthetics |
| **Matrix** | Green (#00FF41) | Digital rain green, hacker aesthetic |
| **Cyber** | Pink/Cyan (#FF007F) | Synthwave sunset with neon glow |
| **Darcula** | Orange (#CC7832) | IDE-inspired dark theme |

Themes are stored in `config.json` and persist across sessions.

### 🧭 Smart Navigation
- **Focus-Locked System**: Context-aware navigation prevents "focus traps"
- **High-Contrast Feedback**: Active tabs use theme-defined colors for clear indication
- **Adaptive Layout**: Automatically detects terminal width and adjusts (hides sidebar on narrow terminals)

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language** | Python 3.12+ |
| **UI Framework** | `prompt_toolkit` (Layouts, Keybindings, Input) |
| **Styling** | `rich` (Tables, Panels, Text rendering) |
| **System Metrics** | `psutil` (CPU/RAM/Network), `WMI` / `GPUtil` (GPU) |
| **Asyncio** | Non-blocking background updates |
| **Configuration** | JSON (`config.json`) |

---

## 🚀 Installation & Usage

### Prerequisites
- Python 3.12 or higher
- Windows Terminal (recommended for TrueColor support)

### Setup
```cmd
# Create virtual environment
python -m venv .venv

# Install dependencies
.venv\Scripts\pip.exe install prompt_toolkit rich psutil
```

### Running the App
```cmd
run.bat
```

> [!NOTE]
> The launch script performs an **Atomic Reset**—forcing the console to 120x30, clearing the buffer, and resetting the cursor position before the application starts.

### Controls
| Key | Action |
| :--- | :--- |
| `q` | Quit the application |
| `Tab` | Toggle focus between **Content** and **Tabs** |
| `←` / `→` | Switch between **Processes**, **Performance**, **Startup** tabs |
| `↑` / `↓` | Navigate through lists (when in Content focus) |

### Theme Commands
```bash
/theme --list              # Show available themes
/theme --style cyber       # Switch to Cyber theme (persists to config.json)
```

---

## 🏗️ Technical Architecture

### Modular Design
The application follows a strict separation of concerns:

```
screens/       # Screen logic and data coordination
  ├── taskmgr_screen.py   # Main Task Manager interface
  ├── cmd_screen.py       # Command input and output handling
  └── intro_screen.py     # Startup/logo screen

modules/
  ├── tabs/       # Tab implementations
  │   ├── processes_tab.py    # Process list with CPU tracking
  │   ├── performance_tab.py  # 2x2 monitor grid
  │   └── startup_tab.py      # Startup applications
  ├── monitors/   # System metric monitors
  │   ├── base_monitor.py    # Base class with rendering
  │   ├── cpu_monitor.py
  │   ├── ram_monitor.py
  │   ├── gpu_monitor.py
  │   └── net_monitor.py
  └── panels/    # Additional UI panels
      └── detail_panel.py

functions/      # Command handlers
  └── theme/    # Theme management

components/     # Reusable UI widgets
  ├── input_area.py
  ├── logo.py
  ├── tips.py
  └── completer.py
```

### Performance Optimizations

1. **Dirty Flag System**: UI only re-renders when data actually changes
2. **ANSI Content Caching**: Rich renderables are converted to ANSI strings once and cached
3. **Process Object Persistence**: `psutil.Process` objects are cached by PID to enable accurate CPU delta calculations
4. **Background Threading**: Heavy system metrics (thread/handle counts) run in a background daemon thread
5. **Oneshot Batching**: Uses `psutil.Process.oneshot()` for efficient batch retrieval of process attributes

---

## 📁 Project Structure

```
myworld.py              # Entry point, main app loop
config.json             # Theme and window settings
run.bat                 # Launch script
README.md               # This file
├── components/          # UI widgets
│   ├── input_area.py   # Command input with history
│   ├── logo.py         # Gradient logo generation
│   ├── tips.py         # Tips display
│   ├── completer.py    # Command autocomplete
│   └── footer.py       # Footer display
├── screens/             # Screen logic
│   ├── taskmgr_screen.py
│   ├── cmd_screen.py
│   └── intro_screen.py
├── layout/              # Layout definitions
│   └── taskmgr_layout.py
├── modules/
│   ├── tabs/            # Tab implementations
│   │   ├── processes_tab.py
│   │   ├── performance_tab.py
│   │   └── startup_tab.py
│   ├── monitors/        # System monitors
│   │   ├── base_monitor.py
│   │   ├── cpu_monitor.py
│   │   ├── ram_monitor.py
│   │   ├── gpu_monitor.py
│   │   └── net_monitor.py
│   └── panels/          # UI panels
│       └── detail_panel.py
├── functions/           # Command handlers
│   ├── theme/
│   ├── system/
│   ├── sysinfo/
│   ├── help.py
│   └── quit.py
├── utils/               # Utilities
│   └── clipboard_manager.py
└── template/            # Response templates
    └── result_response.py
```

---

## 🔧 Configuration

`config.json` controls application behavior:

```json
{
    "theme": "matrix",
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
    }
}
```

---

*Built with ❤️ for the Command Line.*
