"""Shared palette, type and drawing helpers for the profile's SVG assets.

Everything here is plain string building with the standard library, so the
generators run anywhere Python 3.10+ does (locally or on an Actions runner).
"""

from __future__ import annotations

from xml.sax.saxutils import escape

# Palette. Neon is reserved for things that carry meaning; most of the canvas
# is midnight navy and muted slate.
INK = "#05070F"        # deepest background
NAVY = "#0A0F1F"       # panels
NAVY_2 = "#111831"     # raised surfaces
LINE = "#1C2442"       # hairlines, grid
LINE_2 = "#2C3760"     # borders
MUTED = "#7A86AD"      # secondary text
TEXT = "#E4E8F7"       # primary text
CYAN = "#00E5FF"       # primary accent
CYAN_DIM = "#0B8FA6"
PURPLE = "#A855F7"     # secondary accent
MAGENTA = "#FF2E88"    # highlights
AMBER = "#FFB020"      # warnings only

# Mid-tone variants that stay legible on both GitHub's light and dark pages,
# used by the transparent section headers.
CYAN_MID = "#00A9C4"
PURPLE_MID = "#8B5CF6"
MAGENTA_MID = "#E0267A"
SLATE_MID = "#6B7699"

MONO = "'JetBrains Mono','SF Mono',SFMono-Regular,Menlo,Consolas,'DejaVu Sans Mono','Liberation Mono',monospace"
SANS = "'Inter','Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Arial,sans-serif"


def svg_open(w: float, h: float, label: str, extra: str = "") -> str:
    label = escape(label)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{label}"{extra}>\n'
        f"<title>{label}</title>\n"
    )


def text(x, y, s, size=12, fill=TEXT, family=MONO, anchor="start", weight=None,
         spacing=None, opacity=None, cls=None, extra="") -> str:
    attrs = [f'x="{x:g}"', f'y="{y:g}"', f'font-family="{family}"', f'font-size="{size}"',
             f'fill="{fill}"']
    if anchor != "start":
        attrs.append(f'text-anchor="{anchor}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if spacing is not None:
        attrs.append(f'letter-spacing="{spacing}"')
    if opacity is not None:
        attrs.append(f'opacity="{opacity}"')
    if cls:
        attrs.append(f'class="{cls}"')
    return f"<text {' '.join(attrs)}{extra}>{escape(str(s))}</text>"


def chamfer(x, y, w, h, c=10, corners="tl,br") -> str:
    """Polygon points for a rectangle with 45-degree cut corners."""
    cut = set(corners.split(","))
    pts = []
    pts += [(x + c, y)] if "tl" in cut else [(x, y)]
    pts += [(x + w - c, y), (x + w, y + c)] if "tr" in cut else [(x + w, y)]
    pts += [(x + w, y + h - c), (x + w - c, y + h)] if "br" in cut else [(x + w, y + h)]
    pts += [(x + c, y + h), (x, y + h - c)] if "bl" in cut else [(x, y + h)]
    if "tl" in cut:
        pts += [(x, y + c)]
    return " ".join(f"{px:g},{py:g}" for px, py in pts)


# --- Display face -----------------------------------------------------------
# A small hand-drawn angular face for the name, built from strokes on a 4x6
# grid. Drawing it as paths means it renders identically everywhere, without
# depending on whatever fonts the viewer has installed.
GLYPHS: dict[str, list[list[tuple[float, float]]]] = {
    "O": [[(1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0)]],
    "M": [[(0, 6), (0, 0), (2, 2.6), (4, 0), (4, 6)]],
    "K": [[(0, 0), (0, 6)], [(4, 0), (1.6, 3), (0, 3)], [(1.6, 3), (4, 6)]],
    "A": [[(0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)], [(0, 3.6), (4, 3.6)]],
    "R": [[(0, 6), (0, 0), (3, 0), (4, 1), (4, 2.6), (3, 3.6), (0, 3.6)], [(2.4, 3.6), (4, 5.2), (4, 6)]],
    "J": [[(1.4, 0), (4, 0), (4, 5), (3, 6), (1, 6), (0, 5), (0, 4.2)]],
    "S": [[(4, 1.2), (4, 1), (3, 0), (1, 0), (0, 1), (0, 2.2), (0.8, 3), (3.2, 3), (4, 3.8), (4, 5), (3, 6), (1, 6), (0, 5), (0, 4.8)]],
    "H": [[(0, 0), (0, 6)], [(4, 0), (4, 6)], [(0, 3), (4, 3)]],
    "I": [[(0.8, 0), (3.2, 0)], [(2, 0), (2, 6)], [(0.8, 6), (3.2, 6)]],
    " ": [],
}


def glyph_path(word: str, x: float, y: float, unit: float, tracking: float = 1.6) -> str:
    """SVG path data for `word` in the display face, top-left at (x, y)."""
    d = []
    cx = x
    for ch in word.upper():
        for stroke in GLYPHS[ch]:
            pts = " L".join(f"{cx + px * unit:.1f},{y + py * unit:.1f}" for px, py in stroke)
            d.append(f"M{pts}")
        cx += (4 + tracking) * unit
    return " ".join(d)


def glyph_width(word: str, unit: float, tracking: float = 1.6) -> float:
    return (len(word) * (4 + tracking) - tracking) * unit
