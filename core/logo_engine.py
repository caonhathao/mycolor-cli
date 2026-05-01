import io
from typing import Optional

from rich.align import Align
from rich.color import Color
from rich.console import Console
from rich.style import Style
from rich.text import Text

from core.config_manager import get_manager
from core.theme_engine import get_current_theme_colors
from ui.styles.logo_styles import LOGO_STYLES_RAW


LOGO_WORD = "MYCOLOR"
LOGO_HEIGHT = 7
CHAR_SPACING = 2


def _parse_hex6(hex_str: str) -> tuple[int, int, int]:
    s = hex_str.lstrip("#")
    if len(s) >= 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    return (0, 0, 0)


def interpolate_hex(hex1: str, hex2: str, ratio: float) -> str:
    r1, g1, b1 = _parse_hex6(hex1)
    r2, g2, b2 = _parse_hex6(hex2)
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


def _get_hex(s) -> str:
    if isinstance(s, str):
        return s
    if s and hasattr(s, "color") and s.color:
        try:
            t = s.color.get_truecolor()
            return f"#{t.red:02x}{t.green:02x}{t.blue:02x}"
        except Exception:
            pass
    return "#A9B7C6"


class LogoEngine:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @staticmethod
    def get_logo_style():
        cfg = get_manager()
        style = cfg.get_nested("customs", "logo_style", default="gradient")
        if isinstance(style, str):
            return style
        return "gradient"

    @staticmethod
    def set_logo_style(style: str) -> bool:
        cfg = get_manager()
        customs = cfg.get_customs()
        customs["logo_style"] = style
        return cfg.update_section("customs", customs)

    @staticmethod
    def get_available_styles() -> list[str]:
        return list(LOGO_STYLES_RAW.keys())

    @staticmethod
    def render_logo(width: int) -> Text:
        style_name = LogoEngine.get_logo_style()
        colors = get_current_theme_colors()
        style_cfg = LOGO_STYLES_RAW.get(style_name, LOGO_STYLES_RAW["gradient"])

        if style_name == "gradient":
            return LogoEngine._render_gradient(width, colors, style_cfg)
        elif style_name == "minimal":
            return LogoEngine._render_minimal(width, colors, style_cfg)
        elif style_name == "dither":
            return LogoEngine._render_dither(width, colors, style_cfg)
        return LogoEngine._render_gradient(width, colors, style_cfg)

    @staticmethod
    def _calc_geometry(logo_word: str, logo_map: dict, spacing: int) -> tuple[int, int]:
        total_w = 0
        for ch in logo_word:
            pixels = logo_map.get(ch.upper(), [])
            if pixels:
                total_w += len(pixels[0]) + spacing
        return total_w, LOGO_HEIGHT

    @staticmethod
    def _render_gradient(width: int, colors: dict, style_cfg: dict) -> Text:
        logo_map = style_cfg["logo_map"]
        logo_char = style_cfg["logo_char"]
        shadow_char = style_cfg["shadow_char"]
        bg_hex = colors.get("background", "#2B2B2B")

        gradient_colors_raw = colors.get("logo_gradient")
        if gradient_colors_raw and isinstance(gradient_colors_raw, list) and len(gradient_colors_raw) >= 2:
            gradient_hex = [_get_hex(c) for c in gradient_colors_raw]
        else:
            gradient_hex = [_get_hex(colors.get("primary")), _get_hex(colors.get("secondary", colors.get("primary")))]

        shadow_hex = colors.get("logo_shadow", "#555555")
        if isinstance(shadow_hex, str) and shadow_hex.startswith("#"):
            pass
        else:
            try:
                c = Color.parse(shadow_hex)
                t = c.get_truecolor()
                shadow_hex = f"#{t.red:02x}{t.green:02x}{t.blue:02x}"
            except Exception:
                shadow_hex = "#555555"

        total_w, height = LogoEngine._calc_geometry(LOGO_WORD, logo_map, CHAR_SPACING)
        start_x = max(0, (width - total_w) // 2)

        def get_color(ratio):
            n = len(gradient_hex)
            if n < 2:
                return gradient_hex[0]
            seg = 1.0 / (n - 1)
            idx = min(int(ratio / seg), n - 2)
            idx = max(0, idx)
            sub = (ratio - idx * seg) / seg if seg > 0 else 0
            return interpolate_hex(gradient_hex[idx], gradient_hex[idx + 1], sub)

        bg_style = Style(bgcolor=Color.parse(bg_hex))
        grid = [[(" ", bg_style) for _ in range(width)] for _ in range(height)]

        cx = 0
        for ch in LOGO_WORD:
            pixels = logo_map.get(ch.upper(), [])
            if not pixels:
                cx += 5 + CHAR_SPACING
                continue
            char_w = len(pixels[0])
            for y in range(height):
                for x in range(char_w):
                    if pixels[y][x] != " ":
                        gx = cx + x
                        ratio = gx / (total_w - 1) if total_w > 1 else 0.5
                        color = get_color(ratio)
                        style = Style(color=Color.parse(color), bgcolor=Color.parse(bg_hex))
                        gx2 = start_x + gx
                        if 0 <= gx2 < width:
                            grid[y][gx2] = (logo_char, style)
            cx += char_w + CHAR_SPACING

        shadow_off_x, shadow_off_y = 1, 1
        buf_h = height + shadow_off_y
        buf_w = width
        final_grid = [[(" ", bg_style) for _ in range(buf_w)] for _ in range(buf_h)]

        shadow_style = Style(color=Color.parse(shadow_hex), bgcolor=Color.parse(bg_hex))
        for y in range(height):
            for x in range(width):
                ch, _ = grid[y][x]
                if ch != " ":
                    sx = x + shadow_off_x
                    sy = y + shadow_off_y
                    if 0 <= sx < buf_w and 0 <= sy < buf_h:
                        final_grid[sy][sx] = (shadow_char, shadow_style)

        for y in range(height):
            for x in range(width):
                ch, st = grid[y][x]
                if ch != " ":
                    if 0 <= x < buf_w:
                        final_grid[y][x] = (ch, st)

        result = Text()
        for y in range(buf_h):
            for x in range(buf_w):
                ch, st = final_grid[y][x]
                result.append(ch, style=st)
            if y < buf_h - 1:
                result.append("\n")
        return result

    @staticmethod
    def _render_minimal(width: int, colors: dict, style_cfg: dict) -> Text:
        logo_map = style_cfg["logo_map"]
        logo_char = style_cfg["logo_char"]
        bg_hex = colors.get("background", "#2B2B2B")
        primary = colors.get("primary", "#A9B7C6")

        total_w, height = LogoEngine._calc_geometry(LOGO_WORD, logo_map, CHAR_SPACING)
        start_x = max(0, (width - total_w) // 2)

        bg_style = Style(bgcolor=Color.parse(bg_hex))
        ch_style = Style(color=Color.parse(primary), bgcolor=Color.parse(bg_hex))
        grid = [[(" ", bg_style) for _ in range(width)] for _ in range(height)]

        cx = 0
        for ch in LOGO_WORD:
            pixels = logo_map.get(ch.upper(), [])
            if not pixels:
                cx += 5 + CHAR_SPACING
                continue
            char_w = len(pixels[0])
            for y in range(height):
                for x in range(char_w):
                    if pixels[y][x] != " ":
                        gx = start_x + cx + x
                        if 0 <= gx < width:
                            grid[y][gx] = (logo_char, ch_style)
            cx += char_w + CHAR_SPACING

        result = Text()
        for y in range(height):
            for x in range(width):
                ch, st = grid[y][x]
                result.append(ch, style=st)
            if y < height - 1:
                result.append("\n")
        return result

    @staticmethod
    def _render_dither(width: int, colors: dict, style_cfg: dict) -> Text:
        logo_lines = style_cfg["logo_lines"]
        shadow_char = "▓"
        bg_hex = colors.get("background", "#2B2B2B")
        primary_hex = colors.get("primary", "#A9B7C6")
        shadow_hex = colors.get("inactive_tab", "#555555")

        height = len(logo_lines)
        logo_w = max(len(line) for line in logo_lines) if logo_lines else 0
        start_x = max(0, (width - logo_w) // 2)

        bg_style = Style(bgcolor=Color.parse(bg_hex))
        primary_style = Style(color=Color.parse(primary_hex), bgcolor=Color.parse(bg_hex))
        dither_style = Style(color=Color.parse(shadow_hex), bgcolor=Color.parse(bg_hex))

        buf_h = height + 1
        buf_w = width
        final_grid = [[(" ", bg_style) for _ in range(buf_w)] for _ in range(buf_h)]

        # 1. Create a mask of where the main logo will be
        logo_mask = [[False for _ in range(buf_w)] for _ in range(buf_h)]
        for y, line in enumerate(logo_lines):
            for x, ch in enumerate(line):
                if ch != " ":
                    gx = start_x + x
                    if 0 <= gx < buf_w:
                        logo_mask[y][gx] = True

        # 2. Draw dithered shadow (shifted down and right by 1) only where logo won't overlap
        for y, line in enumerate(logo_lines):
            for x, ch in enumerate(line):
                if ch != " ":
                    sx = start_x + x + 1
                    sy = y + 1
                    if 0 <= sx < buf_w and 0 <= sy < buf_h and not logo_mask[sy][sx]:
                        final_grid[sy][sx] = (shadow_char, dither_style)

        # 3. Draw main logo (block-text art using original characters)
        for y, line in enumerate(logo_lines):
            for x, ch in enumerate(line):
                if ch != " ":
                    gx = start_x + x
                    if 0 <= gx < buf_w:
                        final_grid[y][gx] = (ch, primary_style)

        result = Text()
        for y in range(buf_h):
            for x in range(buf_w):
                ch, st = final_grid[y][x]
                result.append(ch, style=st)
            if y < buf_h - 1:
                result.append("\n")
        return result


def get_logo_renderable(width: int):
    try:
        logo_text = LogoEngine.render_logo(width)
        return Align.center(logo_text)
    except Exception:
        colors = get_current_theme_colors()
        return Text("MYCOLOR", style=Style(color=colors.get("primary", "#A9B7C6"), bgcolor=colors.get("background", "#2B2B2B")))
