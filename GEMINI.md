# MYWORLD CLI: Project Architecture & AI Guidelines

## 1. Visual Identity Standards (The "Gemini" Aesthetic)
- [cite_start]**Pixel-Block Logo:** Use only the Unicode Full Block character (█) to construct the "MYWORLD" logo[cite: 1, 3]. [cite_start]Standard ASCII fonts (using /, \, |) are strictly forbidden[cite: 2, 4].
- **Double-Weight Strokes:** Vertical stems of all letters (M, Y, W, O, R, L, D) must be exactly TWO (2) blocks wide (██) to achieve a heavy, premium look.
- [cite_start]**Gradient Engine:** Apply a crisp horizontal RGB gradient: Cyan (#00FFFF) → Purple (#8A2BE2) → Pink (#FF69B4)[cite: 1, 4].
- **Mesh Shadow Texture:** Shadows must use a dithered pattern with Unicode Light Shade (░) or Medium Shade (▒). Do not use solid gray.
- [cite_start]**Layout Alignment:** The logo and hero banner must be perfectly centered horizontally using dynamic padding calculated from `console.width`.
- **Full-Bleed Background:** The entire terminal canvas must be filled with the theme background color (#0d1117). Pad all lines with spaces to the full terminal width to prevent black gaps.

## 2. Interface & Interaction Flow
- [cite_start]**Input Framework:** Use `prompt_toolkit` for the interactive input layer and `Rich` for rendering[cite: 6].
- **Cursor Stability:** The text cursor must be a steady Full Block (█) locked INSIDE the rectangular input box. It must never jump to the bottom footer during typing.
- [cite_start]**Input Layout:** The order of elements must be: Centered Logo → Tips Section → Metadata Line → Rectangular Input Box → Pinned Footer.
- [cite_start]**Command Suggestions:** Implement a `/` trigger with a floating menu for: `/monitor`, `/kill`, `/startup`, `/theme`, and `/help`[cite: 6].

## 3. Technical & Performance Requirements
- **Environment:** Target Python 3.12 for maximum stability with `asyncio` and `psutil`.
- **Silent Launch:** Call `os.system('cls/clear')` immediately. [cite_start]No "Launching...", "Bootstrap...", or dependency logs are allowed to be visible.
- [cite_start]**Background Processes:** Fetch system stats (CPU/RAM) in a separate background thread to ensure zero lag in the input area.
- [cite_start]**Theme Pairs:** Cycle through primary/secondary color pairs: Gray/White, Green/Red, Purple/Cyan.

## 4. Maintenance & Self-Healing
- **Clean Crash Policy:** Overwrite `mw_crash.log` on every run (mode 'w'). Never append to old logs to avoid context confusion.
- **Error Capture:** Wrap the main loop in a global `try-except`. If a crash occurs, print a clean error message and log the full traceback to `mw_crash.log`.
- **Fidelity Check:** Before finalizing code, verify that no `Rich` objects (Panels/Align) are passed directly to `prompt_toolkit` widgets without conversion to ANSI strings.

## 5. Developer Context
- **User Profile:** Senior developer experienced in Next.js, NestJS, Prisma, and Unity.
- [cite_start]**Project Goal:** Replacing Windows Task Manager with a highly optimized, aesthetically pleasing AI-driven CLI tool.