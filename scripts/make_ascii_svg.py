"""Left panel: ASCII art that prints itself row by row.

Default: a big "HAPPY GARG" banner (figlet ANSI Shadow), drawn as real shapes
so it looks identical on every machine, no font luck needed.

Portrait mode: pass a photo and it becomes monochrome ASCII instead.
    python scripts/make_ascii_svg.py                 # name banner
    python scripts/make_ascii_svg.py --photo me.jpg  # ASCII portrait

Writes ascii-art.svg in the repo root. STATIC=1 skips the animation.
"""
import argparse
import os
from pathlib import Path

from term import DIM, FAINT, FG, GREEN, TEXT, esc, window

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "ascii-art.svg"
W, H = 370, 372
STATIC = os.environ.get("STATIC") == "1"

ROW_GAP = 0.09   # seconds between rows starting
ROW_DUR = 0.32   # seconds for one row to wipe in
START = 0.35


# ---------------------------------------------------------------- animation
def row_group(i, x0, y0, width, height, inner, begin):
    """Wrap one row in a clip that wipes left to right, with a block cursor riding the edge."""
    if STATIC:
        return f"<g>{inner}</g>"
    cid = f"r{i}"
    end = begin + ROW_DUR
    return f"""<clipPath id="{cid}"><rect x="{x0}" y="{y0 - 1}" width="0" height="{height + 2}">
<animate attributeName="width" from="0" to="{width + 2}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>
<g clip-path="url(#{cid})">{inner}</g>
<rect x="{x0}" y="{y0}" width="{max(4, height * 0.55):.1f}" height="{height}" fill="{GREEN}" opacity="0">
<set attributeName="opacity" to="0.9" begin="{begin:.2f}s"/>
<animate attributeName="x" from="{x0}" to="{x0 + width}" begin="{begin:.2f}s" dur="{ROW_DUR}s" fill="freeze"/>
<set attributeName="opacity" to="0" begin="{end:.2f}s"/></rect>"""


def prompt_line(x, y, cmd, begin):
    """A shell prompt that appears at `begin`."""
    txt = (f'<text x="{x}" y="{y}" font-size="12.5"><tspan fill="{GREEN}">happy@github</tspan>'
           f'<tspan fill="{DIM}"> ~ $ </tspan><tspan fill="{TEXT}">{esc(cmd)}</tspan></text>')
    if STATIC:
        return txt
    return (f'<g opacity="0"><set attributeName="opacity" to="1" begin="{begin:.2f}s"/>{txt}</g>')


def blinking_cursor(x, y, begin):
    if STATIC:
        return f'<rect x="{x}" y="{y - 11}" width="7.5" height="14" fill="{GREEN}"/>'
    return (f'<rect x="{x}" y="{y - 11}" width="7.5" height="14" fill="{GREEN}" opacity="0">'
            f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1.1s" '
            f'begin="{begin:.2f}s" repeatCount="indefinite"/></rect>')


# ------------------------------------------------------------ banner mode
def glyph(ch, x, y, cw, ch_h):
    """Box-drawing 'shadow' characters as double lines."""
    cx, cy, o = x + cw / 2, y + ch_h / 2, 1.9
    L, R, T, B = x, x + cw, y, y + ch_h
    paths = {
        "═": [f"M{L} {cy - o}H{R}", f"M{L} {cy + o}H{R}"],
        "║": [f"M{cx - o} {T}V{B}", f"M{cx + o} {T}V{B}"],
        "╗": [f"M{L} {cy - o}H{cx + o}V{B}", f"M{L} {cy + o}H{cx - o}V{B}"],
        "╔": [f"M{R} {cy - o}H{cx - o}V{B}", f"M{R} {cy + o}H{cx + o}V{B}"],
        "╚": [f"M{cx - o} {T}V{cy + o}H{R}", f"M{cx + o} {T}V{cy - o}H{R}"],
        "╝": [f"M{cx + o} {T}V{cy + o}H{L}", f"M{cx - o} {T}V{cy - o}H{L}"],
    }
    return paths.get(ch, [])


def banner_rows(words, cw=8, chh=14):
    import pyfiglet

    rows = []
    for wi, word in enumerate(words):
        lines = pyfiglet.figlet_format(word, font="ansi_shadow").rstrip("\n").split("\n")
        lines = [l.rstrip() for l in lines if l.strip()]
        rows.append(lines)
    return rows


def build_banner(words=("HAPPY", "GARG")):
    cw, chh = 8, 14
    blocks = banner_rows(words, cw, chh)
    word_gap = 14
    total_h = sum(len(b) for b in blocks) * chh + word_gap * (len(blocks) - 1)

    top_prompt_y = 56
    art_top = top_prompt_y + 22 + (H - 56 - 22 - 60 - total_h) / 2
    parts = [prompt_line(22, top_prompt_y, "figlet happy garg", 0.05)]

    y = art_top
    i = 0
    for b in blocks:
        width = max(len(l) for l in b) * cw
        x0 = (W - width) / 2
        for line in b:
            inner = []
            # merge runs of full blocks into single rects (no seams)
            col = 0
            while col < len(line):
                if line[col] == "█":
                    start = col
                    while col < len(line) and line[col] == "█":
                        col += 1
                    inner.append(f'<rect x="{x0 + start * cw}" y="{y}" width="{(col - start) * cw}" height="{chh}" fill="{FG}"/>')
                    continue
                for d in glyph(line[col], x0 + col * cw, y, cw, chh):
                    inner.append(f'<path d="{d}"/>')
                col += 1
            shapes = "".join(s for s in inner if s.startswith("<rect"))
            lines_ = "".join(s for s in inner if s.startswith("<path"))
            inner_svg = f'{shapes}<g fill="none" stroke="{FAINT}" stroke-width="1.3">{lines_}</g>'
            parts.append(row_group(i, x0, y, len(line) * cw, chh, inner_svg, START + i * ROW_GAP))
            y += chh
            i += 1
        y += word_gap

    done = START + i * ROW_GAP + ROW_DUR
    bottom_y = H - 30
    parts.append(prompt_line(22, bottom_y, "", done))
    parts.append(blinking_cursor(22 + 7.55 * 17, bottom_y, done))
    return "\n".join(parts)


# ----------------------------------------------------------- portrait mode
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)


def prep_photo(path):
    """Isolate the subject, boost local contrast, put it on white."""
    import cv2
    import numpy as np
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    try:
        from rembg import remove  # optional, big dependency
        img = remove(img)
    except Exception:
        pass
    white = Image.new("RGBA", img.size, (255, 255, 255, 255))
    gray = np.array(Image.alpha_composite(white, img).convert("L"))
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def build_portrait(photo, cols=58):
    import numpy as np
    from PIL import Image

    gray = prep_photo(photo)
    h, w = gray.shape
    top, bottom = 56 + 16, H - 44
    avail_h = bottom - top
    char_w = (W - 36) / cols
    char_h = char_w * 1.9
    rows = int(avail_h / char_h)
    rows = min(rows, int(cols * (h / w) / 1.9 * 1.0) or rows)
    small = np.array(Image.fromarray(gray).resize((cols, rows), Image.LANCZOS)) / 255.0
    parts = [prompt_line(22, 56, "cat portrait.txt", 0.05)]
    x0 = 18
    y = top + (avail_h - rows * char_h) / 2
    for i in range(rows):
        line = "".join(RAMP[len(RAMP) - 1 - int(v * (len(RAMP) - 1))] for v in small[i]).rstrip()
        if not line.strip():
            y += char_h
            continue
        txt = (f'<text x="{x0}" y="{y + char_h * 0.8:.1f}" font-size="{char_h * 0.95:.1f}" fill="#d0d7de" '
               f'textLength="{len(line) * char_w:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{esc(line)}</text>')
        parts.append(row_group(i, x0, y, len(line) * char_w, char_h, txt, START + i * 0.06))
        y += char_h
    done = START + rows * 0.06 + ROW_DUR
    parts.append(prompt_line(22, H - 30, "", done))
    parts.append(blinking_cursor(22 + 7.55 * 17, H - 30, done))
    return "\n".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--photo", help="make an ASCII portrait from this photo instead of the name banner")
    args = ap.parse_args()
    body = build_portrait(args.photo) if args.photo else build_banner()
    OUT.write_text(window(W, H, "happy@github: ~", body))
    print(f"wrote {OUT.name}")


if __name__ == "__main__":
    main()
