import json
import os
import shutil
import sys
import threading
from time import monotonic

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import ANSI

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from functions.theme.theme_logic import _get_config_path
from modules.constants import get_theme_primary, get_theme_color, get_colors_dict, THEME_COLORS

def _get_project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


SETTINGS_PATH = os.path.join(_get_project_root(), "config", "settings.json")


def _load_settings():
    if os.path.exists(SETTINGS_PATH):
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "customs" not in data:
                    data["customs"] = _default_settings()["customs"]
                if "shortcuts" not in data:
                    data["shortcuts"] = _default_settings()["shortcuts"]
                if "commands" not in data:
                    data["commands"] = _default_settings()["commands"]
                return data
        except (json.JSONDecodeError, OSError):
            pass
    
    default = _default_settings()
    _save_settings(default)
    return default


def _default_settings():
    return {
        "customs": {
            "theme": "matrix",
            "logo_style": "gradient",
            "show_tips": True,
            "show_logo_shadow": True,
            "cursor_style": "block",
        },
        "shortcuts": {
            "Ctrl+L": "/clear",
            "Alt+Q": "/quit",
            "Alt+C": "clear_input",
            "Shift+Up": "history_prev",
            "Shift+Down": "history_next",
        },
        "commands": {
            "vscode": "code .",
            "ll": "ls -la",
            "grep": "grep --color=auto",
        },
    }


def _save_settings(data):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return True
    except OSError:
        return False


class SettingsInterface:
    TAB_CUSTOM = 0
    TAB_SHORTCUTS = 1
    TAB_COMMANDS = 2

    def __init__(self, app):
        self.app = app
        self.active_tab = 0
        self.running = True
        self.edit_mode = False
        self.edit_key = None
        self.edit_value = ""
        self.pending_changes = {}
        self.terminal_width = shutil.get_terminal_size().columns

        self._settings = _load_settings()
        self._settings_lock = threading.Lock()
        self._data_changed = True

        self.shortcuts_items = list(self._settings.get("shortcuts", {}).items())
        self.commands_items = list(self._settings.get("commands", {}).items())

        self.shortcuts_selected = 0
        self.commands_selected = 0
        self.commands_scroll_offset = 0

    def _ensure_safe_command(self, cmd):
        if not cmd:
            return ""
        if cmd.startswith("/") or cmd in ("clear_input", "history_prev", "history_next"):
            return cmd
        return cmd

    def get_header(self):
        primary_hex = get_theme_primary()
        primary = primary_hex
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)
        title = f"[\033[38;2;{r};{g};{b}m]  MYCOLOR CLI - Settings  [\033[0m"
        content = [
            ("class:header", f"  MYCOLOR CLI - Settings Manager  "),
        ]
        return content

    def get_tabs(self):
        primary_hex = get_theme_primary()
        primary = primary_hex
        content = []
        tab_names = ["Customs", "Shortcuts", "Commands"]
        for i, name in enumerate(tab_names):
            if i == self.active_tab:
                r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)
                content.append(("class:tab-active", f" [{name}] "))
            else:
                content.append(("class:tab-inactive", f" {name} "))
        return content

    def get_content(self):
        table_text = get_theme_color("table_text", THEME_COLORS["table_text"])
        primary = get_theme_primary()
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)

        lines = []
        if self.active_tab == self.TAB_CUSTOM:
            lines = self._render_customs(table_text, r, g, b)
        elif self.active_tab == self.TAB_SHORTCUTS:
            lines = self._render_shortcuts(table_text, r, g, b)
        elif self.active_tab == self.TAB_COMMANDS:
            lines = self._render_commands(table_text, r, g, b)

        return ANSI("\n".join(lines))

    def _render_customs(self, table_text, r, g, b):
        lines = []
        customs = self._settings.get("customs", {})

        lines.append(f"\033[38;2;{r};{g};{b}m  --- VISUAL CUSTOMIZATION ---\033[0m")
        lines.append("")

        theme = customs.get("theme", "matrix")
        logo_style = customs.get("logo_style", "gradient")
        show_tips = customs.get("show_tips", True)
        show_shadow = customs.get("show_logo_shadow", True)
        cursor = customs.get("cursor_style", "block")

        items = [
            ("theme", theme, "UI color scheme (matrix, classic, cyber, darcula)"),
            ("logo_style", logo_style, "Logo rendering style (gradient, flat, neon)"),
            ("show_tips", str(show_tips), "Show tips on intro screen"),
            ("show_logo_shadow", str(show_shadow), "Show shadow effect under logo"),
            ("cursor_style", cursor, "Cursor shape (block, underline, bar)"),
        ]

        for i, (key, val, desc) in enumerate(items):
            if i == 0:
                prefix = "\033[38;2;0;255;136m>>\033[0m"
            else:
                prefix = "  "
            lines.append(f"{prefix} {key}: \033[38;2;{r};{g};{b}m{val}\033[0m  ({desc})")

        return lines

    def _render_shortcuts(self, table_text, r, g, b):
        lines = []
        lines.append(f"\033[38;2;{r};{g};{b}m  --- KEYBOARD SHORTCUTS ---\033[0m")
        lines.append("")
        lines.append(f"  [\033[38;2;0;255;136mKeys\033[0m]          [\033[38;2;{r};{g};{b}mAction\033[0m]")
        lines.append(f"  {'-'*15}        {'-'*30}")

        shortcuts = self._settings.get("shortcuts", {})
        items = list(shortcuts.items())

        for i, (key, action) in enumerate(items):
            if i == self.shortcuts_selected:
                prefix = "\033[38;2;0;255;136m>>\033[0m"
            else:
                prefix = "  "
            if self.edit_mode and i == self.shortcuts_selected and self.edit_key == "shortcuts":
                lines.append(f"{prefix} {key}: \033[38;2;{r};{g};{b}m[\033[31mEDITING: {action}\033[0m]\033[38;2;{r};{g};{b}m\033[0m")
            else:
                lines.append(f"{prefix} {key:<13} \033[38;2;{r};{g};{b}m{action}\033[0m")

        return lines

    def _render_commands(self, table_text, r, g, b):
        lines = []
        lines.append(f"\033[38;2;{r};{g};{b}m  --- COMMAND ALIASES ---\033[0m")
        lines.append("")
        lines.append(f"  [\033[38;2;0;255;136mAlias\033[0m]           [\033[38;2;{r};{g};{b}mCommand\033[0m]")
        lines.append(f"  {'-'*15}        {'-'*40}")

        commands = self._settings.get("commands", {})
        items = list(commands.items())

        visible_height = max(1, shutil.get_terminal_size().lines - 12)
        visible_items = items[self.commands_scroll_offset:self.commands_scroll_offset + visible_height]

        for i, (alias, cmd) in enumerate(visible_items):
            actual_idx = i + self.commands_scroll_offset
            if actual_idx == self.commands_selected:
                prefix = "\033[38;2;0;255;136m>>\033[0m"
            else:
                prefix = "  "

            if self.edit_mode and actual_idx == self.commands_selected and self.edit_key == "commands":
                lines.append(f"{prefix} {alias:<15} \033[38;2;{r};{g};{b}m[\033[31mEDITING: {cmd}\033[0m]\033[38;2;{r};{g};{b}m\033[0m")
            else:
                lines.append(f"{prefix} {alias:<15} \033[38;2;{r};{g};{b}m{cmd}\033[0m")

        if len(items) > visible_height:
            lines.append("")
            lines.append(f"  [\033[33mShowing {self.commands_scroll_offset + 1}-{min(self.commands_scroll_offset + visible_height, len(items))} of {len(items)}\033[0m]")

        return lines

    def get_hints(self):
        primary = get_theme_primary()
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)

        hints = [
            f"  \033[38;2;{r};{g};{b}m<\033[0m\033[38;2;{r};{g};{b}m Left/Right\033[0m: Switch tabs",
            f"  \033[38;2;{r};{g};{b}m<\033[0m\033[38;2;{r};{g};{b}m Up/Down\033[0m: Navigate    ",
            f"  \033[38;2;{r};{g};{b}m<\033[0m\033[38;2;{r};{g};{b}m Enter\033[0m: Edit/Save    ",
            f"  \033[38;2;{r};{g};{b}m<\033[0m\033[38;2;{r};{g};{b}m Alt+S\033[0m: Save all      ",
            f"  \033[38;2;{r};{g};{b}m<\033[0m\033[38;2;{r};{g};{b}m Alt+Q\033[0m: Quit (no save)",
        ]
        return ANSI("\n".join(hints))

    def get_status_bar(self):
        primary = get_theme_primary()
        r, g, b = int(primary[1:3], 16), int(primary[3:5], 16), int(primary[5:7], 16)

        status = "Settings"
        if self.edit_mode:
            status = f"EDIT MODE: Press Enter to confirm"
        elif self.pending_changes:
            status = f"Changes pending: {len(self.pending_changes)}"

        return ANSI(f"  \033[38;2;{r};{g};{b}m{status}\033[0m" + " " * 40)

    def switch_tab(self, direction):
        self.active_tab = (self.active_tab + direction) % 3
        self.reset_selection()
        self._data_changed = True

    def reset_selection(self):
        self.edit_mode = False
        self.edit_key = None
        self.edit_value = ""
        if self.active_tab == self.TAB_SHORTCUTS:
            self.shortcuts_selected = 0
        elif self.active_tab == self.TAB_COMMANDS:
            self.commands_selected = 0
            self.commands_scroll_offset = 0

    def move_selection(self, direction):
        if self.edit_mode:
            return

        if self.active_tab == self.TAB_SHORTCUTS:
            max_idx = len(self.shortcuts_items) - 1
            self.shortcuts_selected = max(0, min(max_idx, self.shortcuts_selected + direction))
        elif self.active_tab == self.TAB_COMMANDS:
            max_idx = len(self.commands_items) - 1
            self.commands_selected = max(0, min(max_idx, self.commands_selected + direction))
            self._update_commands_scroll()

        self._data_changed = True

    def _update_commands_scroll(self):
        visible_height = max(1, shutil.get_terminal_size().lines - 12)
        if self.commands_selected < self.commands_scroll_offset:
            self.commands_scroll_offset = self.commands_selected
        elif self.commands_selected >= self.commands_scroll_offset + visible_height:
            self.commands_scroll_offset = self.commands_selected - visible_height + 1

    def enter_edit_mode(self):
        if self.active_tab == self.TAB_SHORTCUTS and self.shortcuts_items:
            idx = self.shortcuts_selected
            key = self.shortcuts_items[idx][0]
            current = self.shortcuts_items[idx][1]
            self.edit_mode = True
            self.edit_key = ("shortcuts", idx)
            self.edit_value = current
        elif self.active_tab == self.TAB_COMMANDS and self.commands_items:
            idx = self.commands_selected
            key = self.commands_items[idx][0]
            current = self.commands_items[idx][1]
            self.edit_mode = True
            self.edit_key = ("commands", idx)
            self.edit_value = current

        self._data_changed = True

    def update_edit_value(self, char):
        self.edit_value += char
        self._data_changed = True

    def backspace_edit_value(self):
        if self.edit_value:
            self.edit_value = self.edit_value[:-1]
            self._data_changed = True

    def confirm_edit(self):
        if self.edit_mode and self.edit_key:
            category, idx = self.edit_key

            if category == "shortcuts":
                key = self.shortcuts_items[idx][0]
                self._settings["shortcuts"][key] = self._ensure_safe_command(self.edit_value)
                self.shortcuts_items = list(self._settings["shortcuts"].items())
            elif category == "commands":
                key = self.commands_items[idx][0]
                self._settings["commands"][key] = self.edit_value
                self.commands_items = list(self._settings["commands"].items())

            self.edit_mode = False
            self.edit_key = None
            self.edit_value = ""
            self.pending_changes[category] = True

        self._data_changed = True

    def cancel_edit(self):
        self.edit_mode = False
        self.edit_key = None
        self.edit_value = ""
        self._data_changed = True

    def save_all(self):
        with self._settings_lock:
            result = _save_settings(self._settings)
        self.pending_changes.clear()
        self._data_changed = True
        return result

    def has_changes(self):
        return bool(self.pending_changes)