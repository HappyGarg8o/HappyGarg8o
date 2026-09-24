"""Right panel: a neofetch-style info card that prints line by line.

Edit the CARD list below, then run:
    python scripts/make_info_card.py        # writes info-card.svg
STATIC=1 gives a frozen frame (handy for previews).
"""
import os
from pathlib import Path

from term import DIM, FAINT, FG, GREEN, NEON, TEXT, esc, window

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"
W, H = 490, 372
STATIC = os.environ.get("STATIC") == "1"

# (key, value) rows. key=None continues the previous key.
# ("Built", [(name, what), ...]) renders a sub-list.
CARD = [
    ("Name", "Happy Garg"),
    ("Role", "Solo technical founder"),
    ("Study", "B.Tech CSE, Galgotias University ('28)"),
    ("Location", "Faridabad, India"),
    ("Stack", "Swift · SwiftUI · React Native · Expo"),
    (None, "Supabase · Java · SQL · Python · n8n"),
    ("Built", [
        ("Saathi", "companion booking marketplace"),
        ("SpeakUp", "iOS app, Swift Student Challenge"),
        ("ArbScan", "Solana cross-DEX arbitrage scanner"),
        ("Razorpay", "Buildathon 2026 entry"),
    ]),
    ("LinkedIn", "linkedin.com/in/happy-garg"),
]

X_KEY, X_VAL, X_DESC = 24, 118, 204
LINE = 22
FS = 13


def main():
    rows = []  # list of svg snippets, one per printed line
    rows.append(f'<text font-size="14" font-weight="700"><tspan fill="{GREEN}">happy</tspan>'
                f'<tspan fill="{TEXT}">@</tspan><tspan fill="{GREEN}">github</tspan></text>')
    rows.append(f'<text font-size="{FS}" fill="{FAINT}">{"-" * 12}</text>')
    for key, val in CARD:
        if isinstance(val, list):
            first = True
            for name, what in val:
                k = f'<tspan x="{X_KEY}" fill="{GREEN}" font-weight="700">{esc(key)}</tspan>' if first else ""
                rows.append(f'<text font-size="{FS}">{k}'
                            f'<tspan x="{X_VAL}" fill="{NEON}">› </tspan><tspan fill="{FG}">{esc(name)}</tspan>'
                            f'<tspan x="{X_DESC}" fill="{DIM}">{esc(what)}</tspan></text>')
                first = False
            continue
        k = f'<tspan x="{X_KEY}" fill="{GREEN}" font-weight="700">{esc(key)}</tspan>' if key else ""
        rows.append(f'<text font-size="{FS}">{k}<tspan x="{X_VAL}" fill="{TEXT}">{esc(val)}</tspan></text>')

    swatch = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3"]

    top = 58
    body = []
    style = ""
    if not STATIC:
        style = (".ln{opacity:0;animation:in .45s ease-out forwards}"
                 "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}")
    for i, r in enumerate(rows + ["SWATCH"]):
        y = top + i * LINE
        delay = 0.25 + i * 0.11
        if r == "SWATCH":
            y += 8
            r = "".join(f'<rect x="{X_KEY + j * 26}" y="{y - 12}" width="22" height="14" rx="2" fill="{c}"/>'
                        for j, c in enumerate(swatch))
            body.append(f'<g class="ln" style="animation-delay:{delay:.2f}s">{r}</g>')
            continue
        r = r.replace("<text ", f'<text x="{X_KEY}" y="{y}" ', 1)
        body.append(f'<g class="ln" style="animation-delay:{delay:.2f}s">{r}</g>')

    OUT.write_text(window(W, H, "happy@github: ~ / neofetch", "\n".join(body), style=style))
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
