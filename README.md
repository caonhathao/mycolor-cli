# MYCOLOR CLI | Theme Edition

> [!NOTE]
> *Elevating the terminal experience from the mundane to the magnificent.*

> [!NOTE]
> *This project uses only an AI gent to build. No human code.*

**MYCOLOR CLI** is a next-generation terminal interface designed to bring a "new coat of paint" to the command line. Moving away from dull, monochromatic text, it delivers a vibrant, structured, and "premium" UI.

---

## ✨ Key Features

### 📊 Resource Dashboard
A precision-engineered **2x2 Performance Grid** that monitors system health in real-time:
- **CPU & GPU:** Track load with high-resolution history.
- **RAM & Network:** Monitor memory usage and upload/download speeds.
- **Visuals:** Utilizes **Braille-rendered graphs** for granular, high-density data visualization without clutter.

### 📐 Adaptive Layout
- **Strict Geometry:** Built on a mathematically calculated **120x30** blueprint.
- **Pixel-Perfect:** Every spacer, margin, and border is locked to **1-character precision**, ensuring zero clipping or "ghosting" artifacts at the edges of the terminal buffer.

### 🧭 Smart Navigation
- **Focus-Locked System:** Navigation is context-aware to prevent "focus traps."
- **High-Contrast Feedback:** Active tabs glow with **Bold Yellow** or **Inverted colors** to clearly indicate when navigation is enabled.
- **Graceful Degradation:** The layout engine automatically detects terminal width and hides non-essential components (like the Details sidebar) to preserve the integrity of the main graphs.

---

## 🛠️ Tech Stack

- **Language:** Python 3.12+
- **TUI Framework:** `prompt_toolkit` (Rendering Engine, Layouts, Keybindings)
- **System Metrics:** `psutil` (CPU/RAM/Net) & `GPUtil` (GPU)
- **Asynchronous Engine:** `asyncio` for non-blocking, fluid UI updates and background data fetching.
- **Configuration:** JSON-based blueprint system (`config.json`) for layout persistence and state management.

---

## 🚀 Installation & Usage

### Startup
Simply execute the batch file to launch the environment:
```cmd
run.bat
```
> [!NOTE]
> *This script performs an "Atomic Reset"—forcing the console to 120x30, clearing the buffer, and resetting the cursor to (0,0) before the application loop starts.*

> [!IMPORTANT]
> *For the best experient, the launch size of terminal window must be as least 120x30.*

### Usage

### Controls
| Key | Action |
| :--- | :--- |
| **`q`** | Quit the application immediately. |
| **`Tab`** | Toggle focus between the **Main Content** and the **Footer Tabs**. |
| **`←` / `→`** | Switch between **Processes**, **Performance**, and **Startup** tabs (requires Footer focus). |
| **`↑` / `↓`** | Navigate through process lists or startup items (requires Content focus). |

---

## 🏗️ Technical Architecture

The project follows a strict separation of concerns to ensure maintainability:

- **`screens/` (Logic):** Handles data fetching, business logic, and raw content generation (e.g., `taskmgr_screen.py`).
- **`layouts/` (Visuals):** Manages widget placement, container hierarchy, `VSplit`/`HSplit` structures, and focus rules (e.g., `taskmgr_layout.py`).
- **Atomic Reset:** A specialized startup routine in `myworld.py` ensures the TUI renders on a perfectly clean canvas every time, eliminating the "scrollback ghosting" common in Windows Terminal.

---

*Built with ❤️ for the Command Line.*
