"""Render the GitHub contribution calendar as an isometric night city.

One city block per day: weeks run from the far corner (oldest) to the near
corner (most recent), weekdays run across. Days with no contributions are dark
empty lots. Days with contributions become towers:

- height     ~ sqrt(count / peak count), so one big day doesn't flatten the rest
- windows    lit by GitHub's own quartile level (contributionLevel), from
             sparse purple (first quartile) to dense cyan (fourth quartile)
- beacon     a blinking light on the peak day's tower

Output is deterministic for a given calendar (no randomness, no wall-clock
timestamps), so the scheduled workflow only commits when the data changes.

Usage:
    python scripts/build_city.py                     # fetch via GraphQL, write SVG
    python scripts/build_city.py --input cal.json    # render a saved API response

Needs GITHUB_TOKEN (any token that can call the GraphQL API) to fetch.
If fetching fails the existing SVG is left untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from theme import (CYAN, CYAN_DIM, INK, LINE, LINE_2, MAGENTA, MUTED,  # noqa: E402
                   PURPLE, SANS, TEXT, chamfer, svg_open, text)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "generated" / "city.svg"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
  }
}"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2,
          "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}

# Per-level lighting: lit-window share, window colour, rooftop and ground glow.
LIGHT = {
    1: dict(density=0.30, window="#9D6BFF", roof="#1A1838", glow=PURPLE, glow_op=0.20),
    2: dict(density=0.46, window="#6FA8FF", roof="#16203F", glow="#5B8CFF", glow_op=0.24),
    3: dict(density=0.62, window="#3FE0FF", roof="#112A44", glow=CYAN, glow_op=0.28),
    4: dict(density=0.80, window="#B8F6FF", roof="#0F3346", glow=CYAN, glow_op=0.36),
}

# Canvas and projection. The two axes are deliberately unequal (a dimetric
# view) so a 53-week year fits a README-width image without becoming a tower.
W, H = 1000, 520
WEEK = (15.0, 4.7)    # screen offset per week
DAY = (-11.6, 7.4)    # screen offset per weekday
ORIGIN = (128.0, 176.0)
MAX_H = 160.0
MIN_H = 12.0
INSET = 0.15          # gap between blocks, in cell units (the streets)


def project(i: float, j: float, z: float = 0.0) -> tuple[float, float]:
    return (ORIGIN[0] + i * WEEK[0] + j * DAY[0],
            ORIGIN[1] + i * WEEK[1] + j * DAY[1] - z)


def pts(*ps: tuple[float, float]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in ps)


def quad_d(*ps: tuple[float, float]) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in ps) + "Z"


def unit_hash(*parts) -> float:
    """Stable pseudo-random number in [0, 1) derived from the inputs."""
    h = hashlib.blake2b("|".join(map(str, parts)).encode(), digest_size=8).digest()
    return int.from_bytes(h, "big") / 2**64


# --- data -------------------------------------------------------------------

def fetch(login: str, token: str) -> dict:
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body, method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json",
                 "User-Agent": f"{login}-contribution-city"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.load(resp)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "GraphQL error"))
    return payload


def parse(payload: dict) -> list[dict]:
    user = payload["data"]["user"]
    if not user:
        raise RuntimeError("user not found")
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = []
    for i, week in enumerate(weeks):
        for d in week["contributionDays"]:
            dt = date.fromisoformat(d["date"])
            days.append({
                "date": dt,
                "i": i,
                "j": (dt.weekday() + 1) % 7,  # GitHub weeks start on Sunday
                "count": d["contributionCount"],
                "level": LEVELS.get(d["contributionLevel"], 0),
            })
    if not days:
        raise RuntimeError("empty calendar")
    return days


def stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    active = [d for d in days if d["count"]]
    peak = max(days, key=lambda d: (d["count"], d["date"]))
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    return dict(total=total, active=len(active), span=len(days), peak=peak,
                longest=longest, first=days[0]["date"], last=days[-1]["date"])


def height(count: int, peak: int) -> float:
    return MIN_H + (MAX_H - MIN_H) * math.sqrt(count / peak) if count and peak else 0.0


# --- drawing ----------------------------------------------------------------

def building(d: dict, peak: int, flicker: list[int]) -> str:
    i0, i1 = d["i"] + INSET, d["i"] + 1 - INSET
    j0, j1 = d["j"] + INSET, d["j"] + 1 - INSET
    h = height(d["count"], peak)
    light = LIGHT[max(d["level"], 1)]

    a, b, c, e = (project(i0, j0, h), project(i1, j0, h),
                  project(i1, j1, h), project(i0, j1, h))
    out = [
        # +j face (front left) and +i face (front right)
        f'<polygon points="{pts(e, c, project(i1, j1), project(i0, j1))}" fill="url(#faceL)"/>',
        f'<polygon points="{pts(c, b, project(i1, j0), project(i1, j1))}" fill="url(#faceR)"/>',
        f'<polygon points="{pts(a, b, c, e)}" fill="{light["roof"]}"/>',
    ]
    if d["level"] >= 3:
        out.append(f'<polyline points="{pts(e, a, b)}" fill="none" stroke="{CYAN}" '
                   f'stroke-width="0.8" opacity="{0.35 if d["level"] == 3 else 0.7}"/>')

    # Windows: two columns per face, one row every 8px, lit deterministically.
    # They are batched into one path per face to keep the file small, and
    # emitted with their tower so nearer towers still cover them correctly.
    windows: dict[str, list[str]] = {"L": [], "R": []}
    rows = int((h - 8) // 8)
    for face in ("L", "R"):
        for r in range(rows):
            z = 6 + r * 8
            for col in range(2):
                roll = unit_hash(d["date"], face, r, col)
                if roll >= light["density"]:
                    continue
                u0 = 0.18 + col * 0.38
                u1 = u0 + 0.2
                if face == "L":
                    p = [project(i0 + u0 * (i1 - i0), j1, z), project(i0 + u1 * (i1 - i0), j1, z),
                         project(i0 + u1 * (i1 - i0), j1, z + 3.2), project(i0 + u0 * (i1 - i0), j1, z + 3.2)]
                else:
                    p = [project(i1, j1 - u0 * (j1 - j0), z), project(i1, j1 - u1 * (j1 - j0), z),
                         project(i1, j1 - u1 * (j1 - j0), z + 3.2), project(i1, j1 - u0 * (j1 - j0), z + 3.2)]
                # A small, fixed share of windows flicker; the rest stay still.
                if roll < 0.035 and flicker[0] < 14:
                    flicker[0] += 1
                    out.append(f'<path class="fl fl{flicker[0] % 3}" d="{quad_d(*p)}" '
                               f'fill="{light["window"]}"/>')
                else:
                    windows[face].append(quad_d(*p))
    for face, ds in windows.items():
        if ds:
            out.append(f'<path d="{"".join(ds)}" fill="{light["window"]}" '
                       f'opacity="{0.95 if face == "L" else 0.7}"/>')
    return "\n".join(out)


def beacon(d: dict, peak: int) -> str:
    h = height(d["count"], peak)
    top = project(d["i"] + 0.5, d["j"] + 0.5, h)
    tip = (top[0], top[1] - 16)
    return (f'<line x1="{top[0]:.1f}" y1="{top[1]:.1f}" x2="{tip[0]:.1f}" y2="{tip[1]:.1f}" '
            f'stroke="{MUTED}" stroke-width="1"/>'
            f'<circle class="beacon" cx="{tip[0]:.1f}" cy="{tip[1]:.1f}" r="2.4" fill="{MAGENTA}"/>'
            f'<circle class="beacon" cx="{tip[0]:.1f}" cy="{tip[1]:.1f}" r="7" fill="{MAGENTA}" '
            f'opacity="0.25" filter="url(#soft)"/>')


def legend(days: list[dict], x: float, y: float) -> str:
    out = [text(x, y, "LEGEND", 10, MUTED, spacing=2)]
    # Each swatch is a tiny tower drawn with the real level colours; the count
    # range under it comes from this year's data, so the key never lies.
    ranges = {}
    for d in days:
        if d["level"]:
            lo, hi = ranges.get(d["level"], (d["count"], d["count"]))
            ranges[d["level"]] = (min(lo, d["count"]), max(hi, d["count"]))
    items = [(0, "0", "empty lot")] + [
        (lv, f"{ranges[lv][0]}" if ranges[lv][0] == ranges[lv][1] else f"{ranges[lv][0]}–{ranges[lv][1]}",
         f"Q{lv}") for lv in sorted(ranges)]
    sx = x
    for lv, rng, name in items:
        bx, by = sx + 12, y + 46
        hh = 6 + lv * 7
        w2, d2 = 9, 5  # half-width, half-depth of the swatch footprint
        if lv == 0:
            out.append(f'<polygon points="{pts((bx, by - d2), (bx + w2, by), (bx, by + d2), (bx - w2, by))}" '
                       f'fill="#0E1530" stroke="{LINE_2}" stroke-width="0.6"/>')
        else:
            win = LIGHT[lv]["window"]
            out.append(
                f'<polygon points="{pts((bx - w2, by - hh), (bx, by + d2 - hh), (bx, by + d2), (bx - w2, by))}" fill="#1A2550"/>'
                f'<polygon points="{pts((bx, by + d2 - hh), (bx + w2, by - hh), (bx + w2, by), (bx, by + d2))}" fill="#0E1533"/>'
                f'<polygon points="{pts((bx - w2, by - hh), (bx, by - d2 - hh), (bx + w2, by - hh), (bx, by + d2 - hh))}" fill="{LIGHT[lv]["roof"]}"/>'
            )
            for k in range(lv):
                wy = by - 5 - k * 6
                out.append(f'<rect x="{bx - 6:.1f}" y="{wy:.1f}" width="3" height="2.4" fill="{win}"/>'
                           f'<rect x="{bx + 3:.1f}" y="{wy:.1f}" width="3" height="2.4" fill="{win}" opacity="0.8"/>')
        out.append(text(bx, y + 70, rng, 11, TEXT, anchor="middle"))
        out.append(text(bx, y + 84, name, 9, MUTED, anchor="middle", spacing=1))
        sx += 44
    out.append(text(x, y + 106, "height ∝ √(count ÷ peak)", 10, MUTED))
    out.append(text(x, y + 120, "light = GitHub quartile level", 10, MUTED))
    return "\n".join(out)


def render(days: list[dict]) -> str:
    s = stats(days)
    peak = s["peak"]["count"]
    weeks = days[-1]["i"] + 1

    label = (f"Contribution city: {s['total']} GitHub contributions from {s['first']} to {s['last']} "
             f"drawn as an isometric night city, one block per day. {s['active']} active days; "
             f"peak {peak} on {s['peak']['date']}; longest streak {s['longest']} days.")
    o = [svg_open(W, H, label)]
    o.append(f"""<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="#0B1024"/>
  </linearGradient>
  <radialGradient id="haze" cx="0.55" cy="0.62" r="0.55">
    <stop offset="0" stop-color="#3B1D6E" stop-opacity="0.55"/>
    <stop offset="0.6" stop-color="#1A1240" stop-opacity="0.18"/>
    <stop offset="1" stop-color="{INK}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="ground" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#070A16"/><stop offset="1" stop-color="#0B1128"/>
  </linearGradient>
  <linearGradient id="faceL" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#1D2A58"/><stop offset="1" stop-color="#101734"/>
  </linearGradient>
  <linearGradient id="faceR" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#121A3C"/><stop offset="1" stop-color="#0A0F24"/>
  </linearGradient>
  <filter id="soft" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="3"/></filter>
  <filter id="pool" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="6"/></filter>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">
    <rect width="4" height="1" fill="#FFFFFF" opacity="0.018"/>
  </pattern>
  <clipPath id="frame"><polygon points="{chamfer(0, 0, W, H, 18)}"/></clipPath>
</defs>
<style>
  .fl{{animation:fl 7s steps(1,end) infinite}}
  .fl1{{animation-duration:11s;animation-delay:-3s}}
  .fl2{{animation-duration:5s;animation-delay:-1.5s}}
  @keyframes fl{{0%,100%{{opacity:1}}12%{{opacity:.15}}14%{{opacity:1}}61%{{opacity:.4}}64%{{opacity:1}}}}
  .beacon{{animation:bk 2.4s ease-in-out infinite}}
  @keyframes bk{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}
  @media (prefers-reduced-motion:reduce){{.fl,.beacon{{animation:none}}}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<rect width="{W}" height="{H}" fill="url(#haze)"/>""")

    # Ground slab, district lines at month boundaries, and empty lots.
    g = [project(-0.3, -0.3), project(weeks + 0.3, -0.3), project(weeks + 0.3, 7.3), project(-0.3, 7.3)]
    o.append(f'<polygon points="{pts(*g)}" fill="url(#ground)" stroke="{LINE}" stroke-width="1"/>')

    month_starts = []
    for d in days:
        if d["date"].day == 1:
            month_starts.append(d)
    for d in month_starts:
        # The boundary runs along the start of that week, through all weekdays.
        a, b = project(d["i"], -0.3), project(d["i"], 7.3)
        o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" '
                 f'stroke="{CYAN_DIM}" stroke-width="0.8" opacity="0.35"/>')
        lx, ly = project(d["i"] + 0.5, 8.4)
        o.append(text(lx, ly, d["date"].strftime("%b").upper(), 9, MUTED, anchor="middle", spacing=1.5))

    lots = []
    for d in days:
        if not d["count"]:
            lots.append(quad_d(project(d["i"] + INSET, d["j"] + INSET), project(d["i"] + 1 - INSET, d["j"] + INSET),
                               project(d["i"] + 1 - INSET, d["j"] + 1 - INSET), project(d["i"] + INSET, d["j"] + 1 - INSET)))
    o.append(f'<path d="{"".join(lots)}" fill="#0E1530"/>')

    active = sorted((d for d in days if d["count"]), key=lambda d: (d["i"] + d["j"], d["i"]))

    # Light pooling on the street under each lit tower.
    for d in active:
        lt = LIGHT[max(d["level"], 1)]
        cx, cy = project(d["i"] + 0.5, d["j"] + 0.5)
        o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="16" ry="7" fill="{lt["glow"]}" '
                 f'opacity="{lt["glow_op"]}" filter="url(#pool)"/>')

    # Traffic: one light on the back avenue (behind the towers)...
    back = [project(weeks + 0.3, -0.12), project(-0.3, -0.12)]
    o.append(f'<circle r="1.6" fill="{MAGENTA}" opacity="0.8"><animateMotion dur="38s" repeatCount="indefinite" '
             f'path="M{back[0][0]:.1f},{back[0][1]:.1f} L{back[1][0]:.1f},{back[1][1]:.1f}"/></circle>')

    flicker = [0]  # flickering windows so far, capped across the whole city
    o.extend(building(d, peak, flicker) for d in active)
    if peak:
        o.append(beacon(s["peak"], peak))

    # ...and one on the front avenue.
    front = [project(-0.3, 7.15), project(weeks + 0.3, 7.15)]
    o.append(f'<circle r="1.8" fill="{CYAN}"><animateMotion dur="26s" repeatCount="indefinite" '
             f'path="M{front[0][0]:.1f},{front[0][1]:.1f} L{front[1][0]:.1f},{front[1][1]:.1f}"/></circle>')

    if peak:  # a quiet year has no peak to label
        px, py = project(s["peak"]["i"] + 0.5, s["peak"]["j"] + 0.5, height(peak, peak) + 16)
        side = -1 if px > W - 140 else 1  # flip the label left near the right edge
        lx, ly = px + side * 26, py - 22
        anchor = "end" if side < 0 else "start"
        o.append(f'<polyline points="{pts((px + side * 4, py - 3), (lx, ly), (lx + side * 8, ly))}" fill="none" '
                 f'stroke="{MAGENTA}" stroke-width="0.8" opacity="0.8"/>')
        o.append(text(lx + side * 12, ly + 3, f"PEAK {peak}", 10, MAGENTA, anchor=anchor, spacing=1.5, weight=600))
        o.append(text(lx + side * 12, ly + 16, s["peak"]["date"].strftime("%d %b %Y").upper(), 9, MUTED,
                      anchor=anchor, spacing=1))

    # Title block (top right) and stats.
    tx = 600
    o.append(text(tx, 44, "SECTOR 09 // CONTRIBUTION CITY", 11, CYAN, spacing=3))
    o.append(text(tx, 64, f"{s['first'].strftime('%d %b %Y')}  →  {s['last'].strftime('%d %b %Y')}".upper(),
                  10, MUTED, spacing=1.5))
    o.append(text(tx, 80, "one block per day · rows run sun → sat, back to front", 10, MUTED, spacing=0.5))
    cols = [(s["total"], "CONTRIBUTIONS"), (s["active"], f"ACTIVE / {s['span']} DAYS"),
            (s["longest"], "LONGEST STREAK")]
    for k, (val, lab) in enumerate(cols):
        x = tx + k * 128
        o.append(f'<line x1="{x}" y1="104" x2="{x}" y2="138" stroke="{LINE_2}" stroke-width="1"/>')
        o.append(text(x + 10, 126, val, 24, TEXT, family=SANS, weight=600))
        o.append(text(x + 10, 140, lab, 8.5, MUTED, spacing=1.2))

    o.append(legend(days, 36, 352))

    o.append(f'<rect width="{W}" height="{H}" fill="url(#scan)"/>')
    o.append("</g>")
    o.append(f'<polygon points="{chamfer(0.5, 0.5, W - 1, H - 1, 18)}" fill="none" stroke="{LINE_2}" stroke-width="1"/>')
    # corner ticks
    o.append(f'<path d="M{W - 60},6 H{W - 24} M{W - 6},24 V60 M6,{H - 60} V{H - 24} M24,{H - 6} H60" '
             f'stroke="{CYAN}" stroke-width="1.4" opacity="0.6"/>')
    o.append("</svg>\n")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--user", default=os.environ.get("GH_USER", "omkarjoshi9"))
    ap.add_argument("--input", type=Path, help="saved GraphQL response to render instead of fetching")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    try:
        if args.input:
            payload = json.loads(args.input.read_text(encoding="utf-8"))
        else:
            token = os.environ.get("CITY_TOKEN") or os.environ.get("GITHUB_TOKEN")
            if not token:
                raise RuntimeError("set GITHUB_TOKEN (or CITY_TOKEN) to fetch contributions")
            payload = fetch(args.user, token)
        days = parse(payload)
    except Exception as exc:  # keep the last good city rather than publish a broken one
        print(f"::warning::contribution city not refreshed: {exc}", file=sys.stderr)
        return 0

    svg = render(days)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    previous = args.out.read_text(encoding="utf-8") if args.out.exists() else ""
    if svg != previous:
        args.out.write_text(svg, encoding="utf-8")
        print(f"wrote {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out} "
              f"({len(svg.encode()) // 1024} KB)")
    else:
        print("city unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
