"""Scrape the public contribution calendar (no token needed) into data/contributions.json.

GitHub serves the same HTML fragment the profile page uses at
https://github.com/users/<user>/contributions
"""
import datetime as dt
import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USER = os.environ.get("GH_USER", "HappyGarg8o")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"


def parse_count(text: str) -> int:
    m = re.search(r"(\d[\d,]*)\s+contribution", text or "")
    return int(m.group(1).replace(",", "")) if m else 0


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    # current streak: count back from today; a quiet "today" doesn't break it yet
    current = 0
    rev = list(reversed(days))
    if rev and rev[0]["count"] == 0:
        rev = rev[1:]
    for d in rev:
        if d["count"] == 0:
            break
        current += 1
    return current, longest


def main():
    url = f"https://github.com/users/{USER}/contributions"
    r = requests.get(url, headers={"User-Agent": f"{USER}-profile-readme"}, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    tips = {t.get("for"): parse_count(t.get_text(" ", strip=True)) for t in soup.find_all("tool-tip")}
    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        if not date:
            continue
        level = int(td.get("data-level", 0) or 0)
        count = tips.get(td.get("id"))
        if count is None:  # markup changed? fall back to the level
            count = level
        days.append({"date": date, "level": level, "count": count})
    days.sort(key=lambda d: d["date"])

    if len(days) < 300:
        sys.exit(f"only parsed {len(days)} days, GitHub markup may have changed; keeping old data")

    h2 = soup.find("h2", id="js-contribution-activity-description")
    total = parse_count(h2.get_text(" ", strip=True)) if h2 else sum(d["count"] for d in days)

    current, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    months = OrderedDict()
    for d in days:
        months[d["date"][:7]] = months.get(d["date"][:7], 0) + d["count"]

    data = {
        "user": USER,
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d"),
        "total": total,
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": current,
        "longest_streak": longest,
        "best_day": best if best["count"] > 0 else None,
        "months": months,
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"{total} contributions, {len(days)} days, streak {current}/{longest}")


if __name__ == "__main__":
    main()
