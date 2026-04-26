import io
import json
import os
import shutil
import socket
import threading

from prompt_toolkit.formatted_text import ANSI, HTML
from rich.console import Console

from modules.constants import (
    get_theme_primary, get_theme_color, THEME_COLORS, get_settings, SETTINGS_PATH, get_colors_dict, ROOT_DIR, get_available_themes
)

_ANSI_BUFFER = io.StringIO()
_ANSI_CONSOLE = Console(file=_ANSI_BUFFER, force_terminal=True, width=120, color_system="truecolor")

EDIT_MODE_COLOR = "#FFFF00"

CURSOR_OPTIONS = ["block", "underline", "bar"]
LOGO_OPTIONS = ["gradient", "minimal", "ascii"]


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

        self.customs_selected = 0
        self.shortcuts_selected = 0
        self.commands_selected = 0
        self.commands_scroll_offset = 0

        self.popup_mode = False
        self.popup_options = get_available_themes()
        self.popup_selected = 0
        self.popup_title = ""

        self.listening_mode = False
        self.pending_shortcut_key = None
        self.pending_shortcut_action = ""

    @property
    def popup_height(self):
        count = len(self.popup_options)
        return count if count > 0 else 1

    def _ensure_safe_command(self, cmd):
        if not cmd:
            return ""
        if cmd.startswith("/") or cmd in ("clear_input", "history_prev", "history_next"):
            return cmd
        return cmd

    def get_header(self):
        primary_hex = get_theme_primary()
        header_text = get_theme_color("header_text", THEME_COLORS["header_text"])
        hostname = socket.gethostname()
        mode_suffix = ""
        if self.popup_mode:
            mode_suffix = " - SELECT"
        elif self.listening_mode:
            mode_suffix = " - LISTENING"
        return [(f"bg:{primary_hex} fg:{header_text} bold", f" SETTINGS MANAGER - {hostname}{mode_suffix} ")]

    def get_content(self):
        _ANSI_BUFFER.seek(0)
        _ANSI_BUFFER.truncate(0)
        
        colors = get_colors_dict()
        primary_hex = colors["primary"]
        r, g, b = int(primary_hex[1:3], 16), int(primary_hex[3:5], 16), int(primary_hex[5:7], 16)

        if self.active_tab == self.TAB_CUSTOM:
            self._render_customs(r, g, b, colors)
        elif self.active_tab == self.TAB_SHORTCUTS:
            self._render_shortcuts(r, g, b, colors)
        elif self.active_tab == self.TAB_COMMANDS:
            self._render_commands(r, g, b, colors)

        return ANSI(_ANSI_BUFFER.getvalue())

    def _render_customs(self, r, g, b, colors):
        customs = self._settings.get("customs", {})
        primary_hex = colors["primary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "#BBBBBB")
        accent = colors.get("accent", "#00FF41")
        edit_bg = "#3B3F41"

        KEY_COL = 18
        VAL_COL = 20
        DESC_COL = 25

        _ANSI_CONSOLE.print(f"[bold #00FFFF]{'SETTING':<{KEY_COL}}[/][bold white]{'VALUE':<{VAL_COL}}[/][bold #00FF88]{'DESCRIPTION':<{DESC_COL}}[/]")
        _ANSI_CONSOLE.print("[dim]" + "─" * (KEY_COL + VAL_COL + DESC_COL) + "[/dim]")

        theme = customs.get("theme", "matrix")
        logo_style = customs.get("logo_style", "gradient")
        show_tips = customs.get("show_tips", True)
        show_shadow = customs.get("show_logo_shadow", True)
        cursor = customs.get("cursor_style", "block")

        items = [
            ("theme", theme, "UI color scheme"),
            ("logo_style", logo_style, "Logo rendering style"),
            ("show_tips", str(show_tips), "Show tips on intro"),
            ("show_logo_shadow", str(show_shadow), "Show logo shadow"),
            ("cursor_style", cursor, "Cursor shape"),
        ]

        for i, (key, val, desc) in enumerate(items):
            is_selected = (i == self.customs_selected)
            row = f"[#00FFFF]{key:<{KEY_COL}}[/][{table_text}]{val:<{VAL_COL}}[/][{accent}]{desc:<{DESC_COL}}[/]"
            if is_selected:
                _ANSI_CONSOLE.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
            else:
                _ANSI_CONSOLE.print(row)

    def _render_shortcuts(self, r, g, b, colors):
        primary_hex = colors["primary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "#BBBBBB")
        accent = colors.get("accent", "#00FF41")

        KEY_COL = 20
        ACTION_COL = 30
        DESC_COL = 35

        _ANSI_CONSOLE.print(f"[bold #00FFFF]{'KEY':<{KEY_COL}}[/][bold white]{'ACTION':<{ACTION_COL}}[/][bold #00FF88]{'DESCRIPTION':<{DESC_COL}}[/]")
        _ANSI_CONSOLE.print("[dim]" + "─" * (KEY_COL + ACTION_COL + DESC_COL) + "[/dim]")

        shortcuts = self._settings.get("shortcuts", {})
        items = list(shortcuts.items())
        descriptions = {
            "/clear": "Clear terminal screen",
            "/quit": "Exit application",
            "clear_input": "Clear command input",
            "history_prev": "Previous command history",
            "history_next": "Next command history",
        }

        for i, (key, action) in enumerate(items):
            is_selected = (i == self.shortcuts_selected)
            desc = descriptions.get(action, "")
            row = f"[#00FFFF]{key:<{KEY_COL}}[/][{table_text}]{action:<{ACTION_COL}}[/][{accent}]{desc:<{DESC_COL}}[/]"
            if is_selected:
                _ANSI_CONSOLE.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
            else:
                _ANSI_CONSOLE.print(row)

        add_row = " < New Shortcut > "
        is_add_selected = (self.shortcuts_selected == len(items))
        row = f"[bold #00FF41]{add_row:<{KEY_COL + ACTION_COL + DESC_COL}}[/]"
        if is_add_selected:
            _ANSI_CONSOLE.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
        else:
            _ANSI_CONSOLE.print(row)

    def _render_commands(self, r, g, b, colors):
        primary_hex = colors["primary"]
        suggestion_bg = colors.get("suggestion_bg", "#21262d")
        table_text = colors.get("table_text", "#BBBBBB")

        ALIAS_COL = 20
        CMD_COL = 35

        _ANSI_CONSOLE.print(f"[bold #00FFFF]{'ALIAS':<{ALIAS_COL}}[/][bold white]{'COMMAND':<{CMD_COL}}[/]")
        _ANSI_CONSOLE.print("[dim]" + "─" * (ALIAS_COL + CMD_COL) + "[/dim]")

        commands = self._settings.get("commands", {})
        items = list(commands.items())

        for i, (alias, cmd) in enumerate(items):
            is_selected = (i == self.commands_selected)
            row = f"[#00FFFF]{alias:<{ALIAS_COL}}[/][{table_text}]{cmd:<{CMD_COL}}[/]"
            if is_selected:
                _ANSI_CONSOLE.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
            else:
                _ANSI_CONSOLE.print(row)

        add_row = " < Add New Command > "
        is_add_selected = (self.commands_selected == len(items))
        row = f"[bold #00FF41]{add_row:<{ALIAS_COL + CMD_COL}}[/]"
        if is_add_selected:
            _ANSI_CONSOLE.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
        else:
            _ANSI_CONSOLE.print(row)

    def get_popup_content(self):
        fragments = []
        for i, option in enumerate(self.popup_options):
            style = "class:popup-selected" if i == self.popup_selected else "class:popup-item"
            fragments.append((style, f" {option} ".ljust(20)))
            fragments.append(("", "\n"))
        return fragments

    def get_tabs(self):
        primary_hex = get_theme_primary()
        tab_names = ["Customs", "Shortcuts", "Commands"]
        
        parts = []
        for i, tab in enumerate(tab_names):
            if i == self.active_tab:
                parts.append(f'<b><span color="{primary_hex}">[{tab}]</span></b>')
            else:
                parts.append(f'<span color="#555555">[{tab}]</span>')
        
        return HTML('  '.join(parts))

    def get_hints(self):
        if self.popup_mode:
            return HTML(
                '<span color="#00FF41">[Up/Down]</span> Navigate  |  '
                '<span color="#00FF41">[Enter]</span> Select  |  '
                '<span color="#00FF41">[Esc/Q]</span> Cancel'
            )
        elif self.listening_mode:
            return HTML(
                '<span color="#FFFF00">Listening...</span> Press key combo  |  '
                '<span color="#00FF41">[Esc/Q]</span> Cancel'
            )
        elif self.edit_mode:
            return HTML(
                '<span color="#00FF41">[Up/Down]</span> Navigate  |  '
                '<span color="#00FF41">[Enter]</span> Edit  |  '
                '<span color="#00FF41">[Del]</span> Delete  |  '
                '<span color="#00FF41">[Esc/Q]</span> Cancel'
            )
        else:
            return HTML(
                '<span color="#00FF41">[Left/Right]</span> Switch Tabs  |  '
                '<span color="#00FF41">[Up/Down]</span> Navigate  |  '
                '<span color="#00FF41">[Enter]</span> Edit  |  '
                '<span color="#00FF41">[Del]</span> Delete  |  '
                '<span color="#00FF41">[Q]</span> Quit'
            )

    def get_system_info(self):
        if self.edit_mode or self.popup_mode or self.listening_mode:
            return HTML('<span color="#FFFF00">EDIT MODE</span>')
        elif self.pending_changes:
            return HTML(f'<span color="#FF8800">{len(self.pending_changes)} changes</span>')
        else:
            hostname = socket.gethostname()
            return HTML(f'<span color="#00FF41">{ROOT_DIR}</span> <span color="#00FF41">|</span> <span color="#00FFFF">{hostname}</span> <span color="#00FF41">|</span> <span color="#00FF41">v0.0.1</span>')

    def switch_tab(self, direction):
        if self.popup_mode or self.listening_mode:
            self.cancel_popup()
            return
            
        old_tab = self.active_tab
        self.active_tab = (self.active_tab + direction) % 3
        
        if old_tab != self.active_tab:
            self.reset_selection()
            self._data_changed = True
            
            if hasattr(self, 'app'):
                self.app.renderer.clear()
                self.app.invalidate()

    def reset_selection(self):
        self.edit_mode = False
        self.edit_key = None
        self.edit_value = ""
        self.popup_mode = False
        self.listening_mode = False
        self.popup_selected = 0
        self.popup_options = get_available_themes()
        
        if self.active_tab == self.TAB_CUSTOM:
            self.customs_selected = 0
        elif self.active_tab == self.TAB_SHORTCUTS:
            self.shortcuts_selected = 0
        elif self.active_tab == self.TAB_COMMANDS:
            self.commands_selected = 0
            self.commands_scroll_offset = 0

    def move_selection(self, direction):
        if self.popup_mode:
            if self.popup_options:
                self.popup_selected = (self.popup_selected + direction) % len(self.popup_options)
            self._data_changed = True
            return

        if self.edit_mode:
            return

        if self.active_tab == self.TAB_CUSTOM:
            customs_items = [
                ("theme", None, None),
                ("logo_style", None, None),
                ("show_tips", None, None),
                ("show_logo_shadow", None, None),
                ("cursor_style", None, None),
            ]
            max_idx = len(customs_items) - 1
            self.customs_selected = max(0, min(max_idx, self.customs_selected + direction))
        elif self.active_tab == self.TAB_SHORTCUTS:
            max_idx = len(self.shortcuts_items)
            self.shortcuts_selected = max(0, min(max_idx, self.shortcuts_selected + direction))
        elif self.active_tab == self.TAB_COMMANDS:
            max_idx = len(self.commands_items)
            self.commands_selected = max(0, min(max_idx, self.commands_selected + direction))
            self._update_commands_scroll()

        self._data_changed = True

    def _update_commands_scroll(self):
        visible_height = max(5, shutil.get_terminal_size().lines - 10)
        if self.commands_selected < self.commands_scroll_offset:
            self.commands_scroll_offset = self.commands_selected
        elif self.commands_selected >= self.commands_scroll_offset + visible_height:
            self.commands_scroll_offset = self.commands_selected - visible_height + 1

    def handle_enter(self):
        if self.popup_mode:
            self.confirm_popup()
            return

        if self.listening_mode:
            return

        customs = self._settings.get("customs", {})
        
        if self.active_tab == self.TAB_CUSTOM:
            customs_keys = ["theme", "logo_style", "show_tips", "show_logo_shadow", "cursor_style"]
            key = customs_keys[self.customs_selected]
            
            if key == "theme":
                self.popup_mode = True
                raw_list = get_available_themes()
                self.popup_options = raw_list
                self.popup_selected = raw_list.index(customs.get("theme", "matrix")) if customs.get("theme", "matrix") in raw_list else 0
                self.popup_title = "SELECT THEME"
                self.edit_key = ("custom", "theme")
            elif key == "cursor_style":
                self.popup_mode = True
                self.popup_options = CURSOR_OPTIONS.copy()
                self.popup_selected = self.popup_options.index(customs.get("cursor_style", "block"))
                self.popup_title = "SELECT CURSOR"
                self.edit_key = ("custom", "cursor_style")
            elif key == "logo_style":
                self.popup_mode = True
                self.popup_options = LOGO_OPTIONS.copy()
                self.popup_selected = self.popup_options.index(customs.get("logo_style", "gradient"))
                self.popup_title = "SELECT LOGO STYLE"
                self.edit_key = ("custom", "logo_style")
            elif key == "show_tips":
                customs["show_tips"] = not customs.get("show_tips", True)
                self._settings["customs"] = customs
                self.save_all()
            elif key == "show_logo_shadow":
                customs["show_logo_shadow"] = not customs.get("show_logo_shadow", True)
                self._settings["customs"] = customs
                self.save_all()
            
            self._data_changed = True

        elif self.active_tab == self.TAB_SHORTCUTS:
            if self.shortcuts_selected == len(self.shortcuts_items):
                self.listening_mode = True
                self.pending_shortcut_key = ""
                self.pending_shortcut_action = ""
                self._data_changed = True
            elif self.shortcuts_items:
                idx = self.shortcuts_selected
                key = self.shortcuts_items[idx][0]
                current = self.shortcuts_items[idx][1]
                self.edit_mode = True
                self.edit_key = ("shortcuts", idx)
                self.edit_value = current
                self._data_changed = True

        elif self.active_tab == self.TAB_COMMANDS:
            if self.commands_selected == len(self.commands_items):
                self.popup_mode = True
                self.popup_options = []
                self.popup_title = "ADD NEW COMMAND"
                self.edit_key = ("command", "add")
                self._data_changed = True
            elif self.commands_items:
                idx = self.commands_selected
                key = self.commands_items[idx][0]
                current = self.commands_items[idx][1]
                self.edit_mode = True
                self.edit_key = ("commands", idx)
                self.edit_value = current
                self._data_changed = True

    def handle_delete(self):
        if self.popup_mode or self.listening_mode:
            self.cancel_popup()
            return

        if self.active_tab == self.TAB_SHORTCUTS:
            if self.shortcuts_items and self.shortcuts_selected < len(self.shortcuts_items):
                idx = self.shortcuts_selected
                key = self.shortcuts_items[idx][0]
                del self._settings["shortcuts"][key]
                self.shortcuts_items = list(self._settings["shortcuts"].items())
                self.shortcuts_selected = min(self.shortcuts_selected, len(self.shortcuts_items) - 1)
                self.save_all()
                self._data_changed = True

        elif self.active_tab == self.TAB_COMMANDS:
            if self.commands_items and self.commands_selected < len(self.commands_items):
                idx = self.commands_selected
                key = self.commands_items[idx][0]
                del self._settings["commands"][key]
                self.commands_items = list(self._settings["commands"].items())
                self.commands_selected = min(self.commands_selected, len(self.commands_items) - 1)
                self.save_all()
                self._data_changed = True

    def confirm_popup(self):
        theme_changed = False
        if not self.edit_key:
            return theme_changed

        category, key = self.edit_key

        if category == "custom":
            self._settings["customs"][key] = self.popup_options[self.popup_selected]
            if key == "theme":
                from functions.theme.theme_logic import apply_theme
                apply_theme(self._settings["customs"][key])
                theme_changed = True
            self.save_all()
        elif category == "command":
            if key == "add":
                alias = "new_alias"
                cmd = "new_command"
                self._settings["commands"][alias] = cmd
                self.commands_items = list(self._settings["commands"].items())
                self.save_all()

        self.cancel_popup()
        return theme_changed

    def cancel_popup(self):
        self.popup_mode = False
        self.listening_mode = False
        self.popup_options = []
        self.popup_selected = 0
        self.edit_key = None
        self._data_changed = True

    def capture_key_combo(self, key_name):
        if self.listening_mode:
            self.pending_shortcut_key = key_name
            self.listening_mode = False
            
            if self.pending_shortcut_key in self._settings.get("shortcuts", {}):
                self.listening_mode = False
                self._data_changed = True
                return False
            
            self._settings["shortcuts"][self.pending_shortcut_key] = "custom_action"
            self.shortcuts_items = list(self._settings["shortcuts"].items())
            self.save_all()
            self._data_changed = True
            return True
        return False

    def update_edit_value(self, char):
        self.edit_value += char
        self._data_changed = True

    def backspace_edit_value(self):
        if self.edit_value:
            self.edit_value = self.edit_value[:-1]
            self._data_changed = True

    def confirm_edit(self):
        if self.edit_mode and self.edit_key:
            category, key_or_idx = self.edit_key

            if category == "shortcuts" and isinstance(key_or_idx, int):
                idx = key_or_idx
                key = self.shortcuts_items[idx][0]
                self._settings["shortcuts"][key] = self._ensure_safe_command(self.edit_value)
                self.shortcuts_items = list(self._settings["shortcuts"].items())
            elif category == "commands" and isinstance(key_or_idx, int):
                idx = key_or_idx
                key = self.commands_items[idx][0]
                self._settings["commands"][key] = self.edit_value
                self.commands_items = list(self._settings["commands"].items())

            self.edit_mode = False
            self.edit_key = None
            self.edit_value = ""
            self.pending_changes[category] = True
            self.save_all()

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