import io

from ui.modules.tabs.base_tab import BaseTab
from rich.console import Console

from core.config_manager import get_manager
from core.theme_engine import get_current_theme_colors
from api.theme_api import get_available_themes


class GeneralTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.config_manager = get_manager()
        self.selected = 0
        self.edit_mode = False
        self.edit_value = ""
        self._ansi_buffer = io.StringIO()
        self._ansi_console = Console(file=self._ansi_buffer, force_terminal=True, width=120, color_system="truecolor")

    def update(self, current_time: float) -> bool:
        return False

    def render(self):
        self._ansi_buffer.seek(0)
        self._ansi_buffer.truncate(0)

        colors = get_current_theme_colors()
        primary_hex = colors["primary"]
        secondary = colors.get("secondary", colors.get("primary", ""))
        suggestion_bg = colors.get("suggestion_bg", colors.get("primary", ""))
        table_text = colors.get("table_text", "white")
        accent = colors.get("tab_accent", colors.get("secondary", ""))
        success = colors.get("success", colors.get("primary", ""))

        KEY_COL = 18
        VAL_COL = 20
        DESC_COL = 25

        self._ansi_console.print(f"[bold {secondary}]{'SETTING':<{KEY_COL}}[/][bold {table_text}]{'VALUE':<{VAL_COL}}[/][bold {accent}]{'DESCRIPTION':<{DESC_COL}}[/]")
        self._ansi_console.print("[dim]" + "─" * (KEY_COL + VAL_COL + DESC_COL) + "[/dim]")

        customs = self.parent._settings.get("customs", {})
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
            is_selected = (i == self.selected)
            row = f"[{secondary}]{key:<{KEY_COL}}[/][{table_text}]{val:<{VAL_COL}}[/][{accent}]{desc:<{DESC_COL}}[/]"
            if is_selected:
                self._ansi_console.print(f"[on {suggestion_bg}]{row}[/on {suggestion_bg}]")
            else:
                self._ansi_console.print(row)

        return self._ansi_buffer.getvalue()

    def move_selection(self, direction):
        self.selected = max(0, min(4, self.selected + direction))

    def handle_enter(self):
        customs = self.parent._settings.get("customs", {})
        items = ["theme", "logo_style", "show_tips", "show_logo_shadow", "cursor_style"]
        key = items[self.selected]

        if key == "theme":
            themes = get_available_themes()
            self.parent.popup_height = len(themes)
            self.parent.popup_mode = True
            self.parent.popup_options = themes
            self.parent.popup_selected = themes.index(customs.get("theme", "matrix")) if customs.get("theme", "matrix") in themes else 0
            self.parent.popup_title = "SELECT THEME"
            self.parent.edit_key = ("custom", "theme")
            if self.parent.app:
                self.parent.app.invalidate()
        elif key == "logo_style":
            self.parent.popup_mode = True
            self.parent.popup_options = ["gradient", "minimal", "ascii"]
            self.parent.popup_selected = self.parent.popup_options.index(customs.get("logo_style", "gradient"))
            self.parent.popup_title = "SELECT LOGO STYLE"
            self.parent.edit_key = ("custom", "logo_style")
        elif key == "cursor_style":
            self.parent.popup_mode = True
            self.parent.popup_options = ["block", "underline", "bar"]
            self.parent.popup_selected = self.parent.popup_options.index(customs.get("cursor_style", "block"))
            self.parent.popup_title = "SELECT CURSOR"
            self.parent.edit_key = ("custom", "cursor_style")
        elif key == "show_tips":
            customs["show_tips"] = not customs.get("show_tips", True)
            self.parent._settings["customs"] = customs
            self.parent.save_all()
        elif key == "show_logo_shadow":
            customs["show_logo_shadow"] = not customs.get("show_logo_shadow", True)
            self.parent._settings["customs"] = customs
            self.parent.save_all()

    def handle_delete(self):
        pass

    def on_activate(self):
        self.selected = 0

    def on_deactivate(self):
        pass
