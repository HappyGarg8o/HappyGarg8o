"""Render data/contributions.json as an animated 53-week heatmap -> contrib-heatmap.svg.

Boxes slide in along diagonals once, then stay put. STATIC=1 skips the animation.
"""
import datetime as dt
import json
import os
from pathlib import Path

from term import BORDER, DIM, FAINT, TEXT, esc, window

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 = neon, reserved for your best day)

W = 860
CELL, PITCH, R = 11.5, 15, 2.5
LEFT, TOP = 50, 62


def fmt_day(iso):
    d = dt.date.fromisoformat(iso)
    return d.strftime("%b ") + str(d.day)


def main():
    data = json.loads(DATA.read_text())
    days = data["days"]
    first = dt.date.fromisoformat(days[0]["date"])
    sunday0 = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    best = data.get("best_day")
    best_count = best["count"] if best else 0

    cells, month_labels = [], []
    last_label_col = -9
    ncols = 0
    for d in days:
        date = dt.date.fromisoformat(d["date"])
        col = (date - sunday0).days // 7
        row = (date.weekday() + 1) % 7
        ncols = max(ncols, col + 1)
        lvl = min(int(d["level"]), 4)
        if best_count and d["count"] == best_count:
            lvl = 5
        x, y = LEFT + col * PITCH, TOP + row * PITCH
        diag = col + row
        title = f'{d["count"]} contribution{"s" if d["count"] != 1 else ""} on {fmt_day(d["date"])}'
        cells.append(f'<rect class="c d{diag}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="{R}" '
                     f'fill="{PALETTE[lvl]}"><title>{esc(title)}</title></rect>')
        # label a month on the week holding its first Sunday
        if row == 0 and date.day <= 7 and col - last_label_col >= 3:
            month_labels.append(f'<text x="{x}" y="{TOP - 9}" fill="{DIM}" font-size="11">{date.strftime("%b")}</text>')
            last_label_col = col

    wk = "".join(f'<text x="{LEFT - 10}" y="{TOP + r * PITCH + 9.5}" text-anchor="end" fill="{DIM}" font-size="10.5">{n}</text>'
                 for r, n in ((1, "Mon"), (3, "Wed"), (5, "Fri")))

    grid_bottom = TOP + 7 * PITCH
    y1 = grid_bottom + 26
    right = LEFT + ncols * PITCH - (PITCH - CELL)

    total_txt = f'{data["total"]:,} contribution{"s" if data["total"] != 1 else ""} in the last year'
    legend_x = right - 6 * (CELL + 3) - 38
    legend = (f'<text x="{legend_x - 8}" y="{y1}" text-anchor="end" fill="{DIM}" font-size="11">Less</text>'
              + "".join(f'<rect x="{legend_x + i * (CELL + 3)}" y="{y1 - 10}" width="{CELL}" height="{CELL}" rx="{R}" fill="{c}"/>'
                        for i, c in enumerate(PALETTE))
              + f'<text x="{legend_x + 6 * (CELL + 3) + 4}" y="{y1}" fill="{DIM}" font-size="11">More</text>')

    stats = [f'current streak {data["current_streak"]}d', f'longest {data["longest_streak"]}d',
             f'active days {data["active_days"]}']
    if best:
        stats.append(f'best day {fmt_day(best["date"])} ({best["count"]})')
    stats.append(f'updated {data["updated"]}')
    y2 = y1 + 22

    body = f"""{''.join(month_labels)}{wk}
<g>{''.join(cells)}</g>
<g class="foot">
<text x="{LEFT}" y="{y1}" fill="{TEXT}" font-size="12.5" font-weight="700">{esc(total_txt)}</text>
{legend}
<line x1="{LEFT}" y1="{y1 + 9}" x2="{right}" y2="{y1 + 9}" stroke="{BORDER}" stroke-dasharray="2 4"/>
<text x="{LEFT}" y="{y2}" fill="{DIM}" font-size="11.5">{esc('  ·  '.join(stats))}</text>
</g>"""

    h = int(y2 + 20)
    style = ""
    if not STATIC:
        maxd = ncols + 7
        step = 0.028
        style = (".c{transform-box:fill-box;animation:drop .5s cubic-bezier(.2,.8,.2,1) both}"
                 "@keyframes drop{from{opacity:0;transform:translateY(-7px) scale(.6)}to{opacity:1;transform:none}}"
                 + "".join(f".d{k}{{animation-delay:{0.15 + k * step:.3f}s}}" for k in range(maxd))
                 + f".foot{{animation:fade .6s ease-out {0.15 + maxd * step:.2f}s both}}"
                 "@keyframes fade{from{opacity:0}to{opacity:1}}"
                 "@media (prefers-reduced-motion:reduce){.c,.foot{animation:none}}")
    OUT.write_text(window(W, h, "happy@github: ~/contributions", body, style=style))
    print(f"wrote {OUT.name} ({ncols} weeks)")


if __name__ == "__main__":
    main()
