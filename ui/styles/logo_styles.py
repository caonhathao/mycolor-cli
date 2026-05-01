# Raw logo style definitions

# Gradient style (current): uses █ for logo, ░ for shadow
GRADIENT_M = [
    "███       ███",
    "████     ████",
    "█████   █████",
    "███ ██ ██ ███",
    "███  ███  ███",
    "███   █   ███",
    "███       ███",
]
GRADIENT_Y = [
    "███     ███",
    " ███   ███ ",
    "  ███ ███  ",
    "   █████   ",
    "    ███    ",
    "    ███    ",
    "    ███    ",
]
GRADIENT_C = [
    "  ██████ ",
    " ██    ██",
    "███      ",
    "███      ",
    "███      ",
    " ██    ██",
    "  ██████ ",
]
GRADIENT_O = [
    "  ███████  ",
    " ███   ███ ",
    "███     ███",
    "███     ███",
    "███     ███",
    " ███   ███ ",
    "  ███████  ",
]
GRADIENT_R = [
    "████████   ",
    "███    ███ ",
    "███    ███ ",
    "████████   ",
    "███  ███   ",
    "███   ███  ",
    "███    ███ ",
]
GRADIENT_L = [
    "███      ",
    "███      ",
    "███      ",
    "███      ",
    "███      ",
    "███      ",
    "████████ ",
]

GRADIENT_LOGO_MAP = {
    "M": GRADIENT_M,
    "Y": GRADIENT_Y,
    "C": GRADIENT_C,
    "O": GRADIENT_O,
    "R": GRADIENT_R,
    "L": GRADIENT_L,
}

# Minimal style: flat, single color, no shadow
MINIMAL_LOGO_MAP = GRADIENT_LOGO_MAP

# Dither style: block-text art for "MYCOLOR" using SteamRIP-style characters
# Exact art provided by user - spells "MYCOLOR" using █, ╗, ╔, ╝, ╚, ║
DITHER_LOGO_LINES = [
    "███╗   ███╗██╗   ██╗ ██████╗  ██████╗ ██╗      ██████╗ ██████╗ ",
    "████╗ ████║╚██╗ ██╔╝██╔════╝ ██╔═══██╗██║     ██╔═══██╗██╔══██╗",
    "██╔████╔██║ ╚████╔╝ ██║      ██║   ██║██║     ██║   ██║██████╔╝",
    "██║╚██╔╝██║  ╚██╔╝  ██║      ██║   ██║██║     ██║   ██║██╔══██╗",
    "██║ ╚═╝ ██║   ██║   ╚██████╗ ╚██████╔╝███████╗╚██████╔╝██║  ██║",
    "╚═╝     ╚═╝   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝ ╚═╝  ╚═╝",
]

LOGO_STYLES_RAW = {
    "gradient": {
        "logo_char": "█",
        "shadow_char": "░",
        "logo_map": GRADIENT_LOGO_MAP,
        "has_gradient": True,
        "has_shadow": True,
    },
    "minimal": {
        "logo_char": "█",
        "shadow_char": None,
        "logo_map": MINIMAL_LOGO_MAP,
        "has_gradient": False,
        "has_shadow": False,
    },
    "dither": {
        "logo_lines": DITHER_LOGO_LINES,
        "shadow_chars": ["▓", "▒", "░"],
        "has_gradient": False,
        "has_shadow": True,
    },
}
