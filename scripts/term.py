"""Shared look for every panel: a dark terminal window with a title bar."""
from html import escape

FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"
FG = "#e6edf3"
TEXT = "#c9d1d9"
DIM = "#8b949e"
FAINT = "#484f58"
GREEN = "#39d353"
NEON = "#69f0a0"


def esc(s: str) -> str:
    return escape(s, quote=True)


def window(w: int, h: int, title: str, body: str, style: str = "", defs: str = "") -> str:
    """Wrap `body` in a terminal window of size w x h."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">
<defs>{defs}</defs>
<style>{style}</style>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
<path d="M1 28 V11 a10 10 0 0 1 10 -10 H{w - 11} a10 10 0 0 1 10 10 V28 Z" fill="{BAR}"/>
<line x1="1" y1="28.5" x2="{w - 1}" y2="28.5" stroke="{BORDER}"/>
<circle cx="18" cy="14.5" r="5.5" fill="#ff5f57"/>
<circle cx="36" cy="14.5" r="5.5" fill="#febc2e"/>
<circle cx="54" cy="14.5" r="5.5" fill="#28c840"/>
<text x="{w / 2}" y="19" text-anchor="middle" fill="{DIM}" font-size="12">{esc(title)}</text>
{body}
</svg>
"""
