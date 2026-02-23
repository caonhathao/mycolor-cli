from rich.text import Text
from rich.style import Style
from rich.color import Color
from rich.align import Align

# Font-safe Unicode: U+2588 FULL BLOCK (█) for logo, U+2591 LIGHT SHADE (░) for shadow.
LOGO_CHAR = "\u2588"   # █
SHADOW_CHAR = "\u2591"  # ░

# --- Logo Generation (all use LOGO_CHAR = █ U+2588) ---
def _blk(n: int) -> str:
    return LOGO_CHAR * n

M_PIXELS = [
    "███       ███",
    "████     ████",
    "█████   █████",
    "███ ██ ██ ███",
    "███  ███  ███",
    "███   █   ███",
    "███       ███",
]

Y_PIXELS = [
    "███     ███",
    " ███   ███ ",
    "  ███ ███  ",
    "   █████   ",
    "    ███    ",
    "    ███    ",
    "    ███    ",
]

W_PIXELS = [
    "███       ███",
    "███       ███",
    "███   █   ███",
    "███  ███  ███",
    "███ ██ ██ ███",
    "█████   █████",
    "███       ███",
]

C_PIXELS = [
    "  ██████ ",
    " ██    ██",
    "███      ",
    "███      ",
    "███      ",
    " ██    ██",
    "  ██████ ",
]

O_PIXELS = [
    "  ███████  ",
    " ███   ███ ",
    "███     ███",
    "███     ███",
    "███     ███",
    " ███   ███ ",
    "  ███████  ",
]

R_PIXELS = [
    "████████   ",
    "███    ███ ",
    "███    ███ ",
    "████████   ",
    "███  ███   ",
    "███   ███  ",
    "███    ███ ",
]

L_PIXELS = [
    "███      ",
    "███      ",
    "███      ",
    "███      ",
    "███      ",
    "███      ",
    "████████ ",
]

D_PIXELS = [
    "████████   ",
    "███    ███ ",
    "███     ███",
    "███     ███",
    "███     ███",
    "███    ███ ",
    "████████   ",
]

LOGO_MAP = {
    "M": M_PIXELS,
    "Y": Y_PIXELS,
    "W": W_PIXELS,
    "C": C_PIXELS,
    "O": O_PIXELS,
    "R": R_PIXELS,
    "L": L_PIXELS,
    "D": D_PIXELS,
}

def _parse_hex6(hex_str: str) -> tuple[int, int, int]:
    """Parse hex string to RGB. Always returns exactly 6-digit hex portion. No alpha."""
    s = hex_str.lstrip("#")
    if len(s) >= 6:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    return (0, 0, 0)


def interpolate_hex(hex1: str, hex2: str, ratio: float) -> str:
    """
    Smooth gradient: interpolate between two hex colors.
    Returns exactly 6-digit hex (#RRGGBB). No alpha.
    """
    r1, g1, b1 = _parse_hex6(hex1)
    r2, g2, b2 = _parse_hex6(hex2)
    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)
    return f"#{r:02x}{g:02x}{b:02x}"


def _generate_logo_grid(logo_word: str, gradient_colors_str: list[str], bg_hex: str, container_width: int = 100) -> tuple[list[list[tuple[str, Style]]], int, int]:
    """
    Generates a 2D grid of (char, Style) tuples for the logo.
    """
    def _ensure_hex6(s: str) -> str:
        h = s.lstrip("#")
        if len(h) >= 6:
            return "#" + h[:6].lower()
        return "#000000"

    gradient_hex = [_ensure_hex6(c) for c in gradient_colors_str]

    # 1. Calculate Geometry
    char_spacing = 2
    chars_pixels = []
    total_width = 0
    height = 7
    
    for char in logo_word:
        pixels = LOGO_MAP.get(char.upper(), [])
        if pixels:
            chars_pixels.append(pixels)
            total_width += len(pixels[0]) + char_spacing
        else:
            # Fallback for unknown chars
            chars_pixels.append([" " * 5] * 7)
            total_width += 5 + char_spacing
            
    # Calculate start_x to center the logo in the container
    start_x = max(0, (container_width - total_width) // 2)
    final_width = container_width

    # 2. Create Grid
    # (y, x) -> (char, Style)
    bg_style = Style(bgcolor=Color.parse(bg_hex))
    grid = [[(" ", bg_style) for _ in range(final_width)] for _ in range(height)]

    # 3. Fill Grid with Gradient
    current_x = 0
    
    def get_color(x_ratio):
        n = len(gradient_hex)
        if n < 2: return gradient_hex[0] if n else "#ffffff"
        segment_len = 1.0 / (n - 1)
        idx = min(int(x_ratio / segment_len), n - 2)
        idx = max(0, idx)
        sub_ratio = (x_ratio - idx * segment_len) / segment_len if segment_len > 0 else 0
        return interpolate_hex(gradient_hex[idx], gradient_hex[idx+1], sub_ratio)

    for pixels in chars_pixels:
        char_w = len(pixels[0])
        for y in range(height):
            for x in range(char_w):
                if pixels[y][x] != " ":
                    # Calculate global x ratio for gradient
                    global_x = current_x + x
                    ratio = global_x / (total_width - 1) if total_width > 1 else 0.5
                    color = get_color(ratio)
                    style = Style(color=Color.parse(color), bgcolor=Color.parse(bg_hex))
                    
                    grid_x = start_x + current_x + x
                    if 0 <= grid_x < final_width:
                        grid[y][grid_x] = (LOGO_CHAR, style)
        current_x += char_w + char_spacing

    return grid, final_width, height

def generate_logo_rich_text(width: int, theme: dict, background_color_hex: str) -> tuple[Text, int]:
    """
    Generates the 'MYCOLOR' pixel art logo with gradient and shadow.
    Uses █ (U+2588) for logo, ░ (U+2591) for shadow. Every character has bg #0d1117 for seamless display.
    """
    word = "MYCOLOR"
    gradient_colors = theme["logo_gradient"]
    # Shadow: font-safe ░ (U+2591). Convert shadow color to 6-digit hex.
    try:
        shadow_color = Color.parse(theme.get("logo_shadow", "grey30"))
        t = shadow_color.get_truecolor()
        shadow_hex = f"#{t.red:02x}{t.green:02x}{t.blue:02x}"
    except Exception:
        shadow_hex = "#404040"
    bg_hex = "#0d1117"
    if background_color_hex and len(background_color_hex.lstrip("#")) >= 6:
        bg_hex = "#" + background_color_hex.lstrip("#")[:6].lower()

    # Force 80 char width for the grid generation to ensure centering
    logo_grid, logo_w, logo_h = _generate_logo_grid(word, gradient_colors, bg_hex, container_width=100)

    shadow_offset_x, shadow_offset_y = 1, 1
    buffer_height = logo_h + shadow_offset_y
    buffer_width = logo_w # The grid is already padded to 80, shadow might clip if we aren't careful, but 80 is wide enough.

    # Final buffer with background
    bg_style = Style(bgcolor=Color.parse(bg_hex))
    final_grid = [[(" ", bg_style) for _ in range(buffer_width)] for _ in range(buffer_height)]

    # 1. Draw Shadow
    try:
        shadow_style = Style(color=Color.parse(shadow_hex), bgcolor=Color.parse(bg_hex))
    except Exception:
        shadow_style = Style(color="grey30", bgcolor=Color.parse(bg_hex))

    for y in range(logo_h):
        for x in range(logo_w):
            char, _ = logo_grid[y][x]
            if char != " ":
                sx = x + shadow_offset_x
                sy = y + shadow_offset_y
                if 0 <= sx < buffer_width and 0 <= sy < buffer_height:
                    final_grid[sy][sx] = (SHADOW_CHAR, shadow_style)

    # 2. Draw Logo (overwrites shadow)
    for y in range(logo_h):
        for x in range(logo_w):
            char, style = logo_grid[y][x]
            if char != " ":
                if 0 <= x < buffer_width:
                    final_grid[y][x] = (char, style)

    final_logo_text = Text()
    for y_line_idx in range(buffer_height):
        for x_char in range(buffer_width):
            char, style = final_grid[y_line_idx][x_char]
            final_logo_text.append(char, style=style)
        if y_line_idx < buffer_height - 1:
            final_logo_text.append("\n")

    return final_logo_text, buffer_height

def get_logo_renderable(console_width: int, theme: dict):
    """Generates the Logo renderable (centered)."""
    background_style = Style(bgcolor=theme["background"])
    try:
        # We force 80 width in generation, so we can just return it.
        # The Align.center in myworld.py is redundant if we generate 80 chars, 
        # but good for safety if console > 80.
        raw_logo_text, _ = generate_logo_rich_text(100, theme, theme["background"])
        return Align.center(raw_logo_text)
    except Exception:
        raw_logo_text = Text(
            "MYWORLD", style=Style(color="#a020f0", bgcolor=theme["background"])
        )
        return raw_logo_text
