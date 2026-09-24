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
    """Wrap one row in a clip that wipes left to right, with a block cursor riding the edge.

    Every animation starts at t=0 and encodes its delay in keyTimes, so the art's
    base state is fully drawn. If a viewer can't run SMIL, it just shows the final frame.
    """
    if STATIC:
        return f"<g>{inner}</g>"
    cid = f"r{i}"
    T = begin + ROW_DUR
    k = begin / T
    cw = max(4, height * 0.55)
    return f"""<clipPath id="{cid}"><rect x="{x0}" y="{y0 - 1}" width="{width + 2}" height="{height + 2}">
<animate attributeName="width" values="0;0;{width + 2}" keyTimes="0;{k:.4f};1" dur="{T:.2f}s" fill="freeze"/></rect></clipPath>
<g clip-path="url(#{cid})">{inner}</g>
<rect x="{x0}" y="{y0}" width="{cw:.1f}" height="{height}" fill="{GREEN}" opacity="0">
<animate attributeName="opacity" values="0;0.9;0" keyTimes="0;{k:.4f};1" calcMode="discrete" dur="{T:.2f}s" fill="freeze"/>
<animate attributeName="x" values="{x0};{x0};{x0 + width}" keyTimes="0;{k:.4f};1" dur="{T:.2f}s" fill="freeze"/></rect>"""


def prompt_line(x, y, cmd, begin):
    """A shell prompt that appears at `begin`."""
    txt = (f'<text x="{x}" y="{y}" font-size="12.5"><tspan fill="{GREEN}">happy@github</tspan>'
           f'<tspan fill="{DIM}"> ~ $ </tspan><tspan fill="{TEXT}">{esc(cmd)}</tspan></text>')
    if STATIC:
        return txt
    return f'<g><animate attributeName="opacity" values="0" dur="{begin:.2f}s"/>{txt}</g>'


def blinking_cursor(x, y, begin):
    rect = f'<rect x="{x}" y="{y - 11}" width="7.5" height="14" fill="{GREEN}"'
    if STATIC:
        return rect + "/>"
    return (rect + f'><animate attributeName="opacity" values="0" dur="{begin:.2f}s"/>'
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
# Light text on a dark terminal: brighter pixels get denser glyphs.
RAMP = " .,:;-=+*oxO#%@"


def prep_photo(path):
    """Cut the subject out, crop to head and shoulders, boost local contrast.

    Returns (gray, mask) as float arrays in 0..1.
    """
    import cv2
    import numpy as np
    from PIL import Image

    img = Image.open(path).convert("RGBA")
    try:
        from rembg import new_session, remove  # optional, big dependency
        img = remove(img, session=new_session("u2net_human_seg"))
    except Exception as e:  # no rembg: keep the photo, use a full mask
        print(f"(rembg unavailable, keeping background: {e})")
    rgba = np.array(img)
    alpha = rgba[:, :, 3].astype(float) / 255
    ys, xs = np.where(alpha > 0.15)
    # centre on the head: the widest rows near the top are the head, not the shoulders
    top_rows = alpha[ys.min(): ys.min() + int(0.45 * (ys.max() - ys.min()))] > 0.5
    hx = np.where(top_rows.any(axis=0))[0]
    cx, head_w = (hx.min() + hx.max()) / 2, hx.max() - hx.min()
    half = int(head_w * CROP_WIDTH / 2)
    x0, x1 = max(0, int(cx - half)), min(alpha.shape[1], int(cx + half))
    y0 = max(0, ys.min() - int(0.02 * head_w))
    y1 = min(rgba.shape[0], y0 + int((x1 - x0) * CROP_ASPECT))
    rgba, alpha = rgba[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

    gray = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(4, 4)).apply(gray)
    # sharpen, then mix in edges so glasses, eyes and jawline survive downsampling
    blur = cv2.GaussianBlur(gray, (0, 0), 3)
    gray = cv2.addWeighted(gray, 1.8, blur, -0.8, 0).astype(float)
    edges = cv2.Canny(cv2.GaussianBlur(rgba[:, :, :3], (0, 0), 1.5), 40, 110).astype(float)
    edges = cv2.GaussianBlur(edges, (0, 0), 2.5)
    inside = gray[alpha > 0.5]
    lo, hi = np.percentile(inside, 5), np.percentile(inside, 99.7)
    gray = np.clip((gray - lo) / (hi - lo), 0, 1) ** 1.2
    gray = np.clip(gray + 0.55 * edges / max(edges.max(), 1), 0, 1)
    return gray, alpha


CROP_ASPECT = 1.12  # crop height / width
CROP_WIDTH = 1.45   # crop width as a multiple of head width


def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


def build_portrait(photo, cols=92):
    import numpy as np
    from PIL import Image

    gray, alpha = prep_photo(photo)
    top, bottom = 56 + 12, H - 40
    char_w = (W - 40) / cols
    char_h = char_w * 1.75
    rows = int(round(cols * CROP_ASPECT * char_w / char_h))
    if rows * char_h > bottom - top:
        rows = int((bottom - top) / char_h)
    g = np.array(Image.fromarray((gray * 255).astype("uint8")).resize((cols, rows), Image.LANCZOS)) / 255
    m = np.array(Image.fromarray((alpha * 255).astype("uint8")).resize((cols, rows), Image.BILINEAR)) / 255

    parts = [prompt_line(22, 56, "cat happy.txt", 0.05)]
    x0 = (W - cols * char_w) / 2
    y = top + (bottom - top - rows * char_h) / 2
    n = len(RAMP) - 1
    levels = 8
    shades = [_mix("#30363d", "#f0f6fc", k / (levels - 1)) for k in range(levels)]
    for i in range(rows):
        cells = []  # (glyph, shade index)
        for v, a in zip(g[i], m[i]):
            if a < 0.35:
                cells.append((" ", 0))
            else:
                cells.append((RAMP[max(1, int(round(v * n)))], min(levels - 1, int(v * levels))))
        while cells and cells[-1][0] == " ":
            cells.pop()
        if any(c != " " for c, _ in cells):
            # one tspan per run of equal shade keeps the file small
            spans, run, cur = [], "", cells[0][1]
            for c, k in cells:
                if k != cur and c != " ":
                    spans.append(f'<tspan fill="{shades[cur]}">{esc(run)}</tspan>')
                    run, cur = "", k
                run += c
            spans.append(f'<tspan fill="{shades[cur]}">{esc(run)}</tspan>')
            txt = (f'<text x="{x0:.1f}" y="{y + char_h * 0.78:.1f}" font-size="{char_h * 0.92:.1f}" '
                   f'textLength="{len(cells) * char_w:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{"".join(spans)}</text>')
            parts.append(row_group(i, x0, y, len(cells) * char_w, char_h, txt, START + i * 0.045))
        y += char_h
    done = START + rows * 0.045 + ROW_DUR
    parts.append(prompt_line(22, H - 22, "", done))
    parts.append(blinking_cursor(22 + 7.55 * 17, H - 22, done))
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
