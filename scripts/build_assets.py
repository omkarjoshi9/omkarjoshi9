"""Build the static SVG assets for the profile README.

    python scripts/build_assets.py

Writes the hero, section headers, tech arsenal panel and contact channels
into assets/. These only change when the design or the facts in them change,
so they are not part of the scheduled workflow. The contribution city lives
in build_city.py.
"""

from __future__ import annotations

from pathlib import Path

from theme import (AMBER, CYAN, INK, LINE, LINE_2, MAGENTA, MONO, MUTED, NAVY, NAVY_2,
                   PURPLE, SANS, TEXT, chamfer, glyph_path, svg_open, text)

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def write(rel: str, svg: str) -> None:
    path = ASSETS / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")
    print(f"wrote assets/{rel} ({len(svg.encode()) / 1024:.1f} KB)")


def skyline(y_base: float, width: float, seed: int, fill: str, lit: str, max_h=70) -> str:
    """A distant, low-contrast silhouette. Decorative backdrop only; the
    data-driven city is a separate asset."""
    out, x, k = [], 0.0, seed
    while x < width:
        k = (k * 1103515245 + 12345) & 0x7FFFFFFF
        w = 14 + k % 26
        h = 12 + (k >> 8) % max_h
        out.append(f'<rect x="{x:.0f}" y="{y_base - h:.0f}" width="{w}" height="{h + 2}" fill="{fill}"/>')
        if (k >> 4) % 3 == 0:
            out.append(f'<rect x="{x + w / 2 - 1:.0f}" y="{y_base - h + 6:.0f}" width="2" height="2" fill="{lit}" opacity="0.5"/>')
        x += w + (k >> 12) % 4
    return "".join(out)


# --- hero -------------------------------------------------------------------

BOOT = [
    # (text, status, status colour)
    ("scope allowlist", "OK", CYAN),
    ("docker sandbox", "OK", CYAN),
    ("request budget", "OK", CYAN),
    ("evidence ledger", "OK", CYAN),
    ("human approval gate", "HOLD", AMBER),
]


def hero() -> str:
    W, H = 1000, 400
    label = ("Omkar Joshi, agentic systems engineer, Pune. A workstation boot screen: the name "
             "in neon, and a boot log that checks the limits his agents run inside: scope "
             "allowlist, Docker sandbox, request budget, evidence ledger, and a human approval gate.")
    o = [svg_open(W, H, label)]
    o.append(f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">
    <stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="#0A0E22"/>
  </linearGradient>
  <radialGradient id="glow" cx="0.22" cy="0.42" r="0.5">
    <stop offset="0" stop-color="#0E3A55" stop-opacity="0.55"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glow2" cx="0.85" cy="1" r="0.55">
    <stop offset="0" stop-color="#3A1460" stop-opacity="0.5"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/>
  </radialGradient>
  <filter id="neon" x="-10%" y="-20%" width="120%" height="140%"><feGaussianBlur stdDeviation="5"/></filter>
  <pattern id="scan" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="1" fill="#fff" opacity="0.022"/></pattern>
  <clipPath id="frame"><polygon points="{chamfer(0, 0, W, H, 22)}"/></clipPath>
</defs>
<style>
  .ln{{animation:in .01s linear both}}
  @keyframes in{{from{{opacity:0}}to{{opacity:1}}}}
  .ig{{animation:ignite 1.1s steps(1,end) both}}
  @keyframes ignite{{0%{{opacity:.08}}18%{{opacity:.9}}24%{{opacity:.15}}42%{{opacity:1}}50%{{opacity:.3}}64%,100%{{opacity:1}}}}
  .cur{{animation:blink 1.1s steps(1,end) infinite}}
  @keyframes blink{{50%{{opacity:0}}}}
  .pulse{{animation:pulse 2.8s ease-in-out infinite}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
  @media (prefers-reduced-motion:reduce){{.ln,.ig,.cur,.pulse{{animation:none}}}}
</style>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect width="{W}" height="{H}" fill="url(#glow)"/>
<rect width="{W}" height="{H}" fill="url(#glow2)"/>""")

    # Backdrop skyline and a horizon line.
    o.append(f'<g opacity="0.9">{skyline(352, W, 7, "#0B1129", "#7C5CFF", 64)}</g>')
    o.append(f'<g opacity="0.95">{skyline(358, W, 23, "#070B1C", CYAN, 34)}</g>')
    o.append(f'<line x1="0" y1="358.5" x2="{W}" y2="358.5" stroke="{LINE_2}" stroke-width="1"/>')

    # Top rail.
    o.append(text(40, 38, "OMKARJOSHI9 // PERSONAL WORKSTATION", 10, MUTED, spacing=3))
    o.append(text(W - 40, 38, "18.52°N  73.86°E", 10, MUTED, anchor="end", spacing=2))
    o.append(f'<line x1="40" y1="50" x2="{W - 40}" y2="50" stroke="{LINE}" stroke-width="1"/>')
    o.append(f'<rect x="40" y="49" width="56" height="2" fill="{CYAN}"/>')

    # Name, in the display face. OMKAR ignites first; JOSHI after the boot log.
    unit, x0 = 12.5, 44
    y1, y2 = 84, 84 + 6 * unit + 26
    om, jo = glyph_path("OMKAR", x0, y1, unit), glyph_path("JOSHI", x0, y2, unit)
    # Unlit tubes underneath, so the sign reads as a sign before it lights.
    o.append(f'<path d="{om} {jo}" fill="none" stroke="#1E2547" stroke-width="4.2" stroke-linecap="square"/>')
    for d, colour, delay in ((om, CYAN, "0.25s"), (jo, MAGENTA, "2.55s")):
        o.append(f'<g class="ig" style="animation-delay:{delay}" fill="none" stroke-linecap="square" stroke-linejoin="miter">'
                 f'<path d="{d}" stroke="{colour}" stroke-width="9" opacity="0.45" filter="url(#neon)"/>'
                 f'<path d="{d}" stroke="{colour}" stroke-width="4.2"/>'
                 f'<path d="{d}" stroke="#F4FEFF" stroke-width="1.3" opacity="0.85"/></g>')

    ty = y2 + 6 * unit + 40
    o.append(text(x0, ty, "AGENTIC SYSTEMS ENGINEER", 14, TEXT, spacing=5.5, weight=600))
    o.append(text(x0, ty + 22, "autonomous agents that run inside hard limits", 12, MUTED, spacing=0.6))

    # Boot terminal.
    tx, ty0, tw, th = 590, 78, 370, 236
    o.append(f'<polygon points="{chamfer(tx, ty0, tw, th, 14, "tr,bl")}" fill="{NAVY}" fill-opacity="0.92" stroke="{LINE_2}"/>')
    o.append(f'<rect x="{tx}" y="{ty0}" width="{tw - 14}" height="24" fill="{NAVY_2}"/>')
    o.append(text(tx + 14, ty0 + 16, "tty1 · boot", 10, MUTED, spacing=1.5))
    for k, c in enumerate((MAGENTA, PURPLE, CYAN)):
        o.append(f'<rect x="{tx + tw - 70 + k * 14}" y="{ty0 + 9}" width="7" height="7" fill="{c}" opacity="0.75"/>')

    lx, ly, step = tx + 18, ty0 + 52, 23
    t = 0.45
    o.append(f'<g class="ln" style="animation-delay:{t:.2f}s">'
             + text(lx, ly, "$", 12, CYAN) + text(lx + 16, ly, "boot --operator omkarjoshi9", 12, TEXT) + "</g>")
    for k, (name, status, colour) in enumerate(BOOT, start=1):
        t += 0.32
        y = ly + k * step
        dots = "." * (24 - len(name))
        o.append(f'<g class="ln" style="animation-delay:{t:.2f}s">'
                 + text(lx + 16, y, f"{name} {dots}", 12, MUTED)
                 + text(tx + tw - 22, y, f"[{status:^4}]", 12, colour, anchor="end", weight=600) + "</g>")
    t += 0.45
    y = ly + (len(BOOT) + 1) * step + 6
    o.append(f'<g class="ln" style="animation-delay:{t:.2f}s">'
             + text(lx, y, "autonomy:", 12, MUTED) + text(lx + 80, y, "bounded", 12, TEXT, weight=600) + "</g>")
    t += 0.35
    y += step
    o.append(f'<g class="ln" style="animation-delay:{t:.2f}s">'
             + text(lx, y, ">", 12, MAGENTA) + text(lx + 16, y, "operator online", 12, TEXT)
             + f'<rect class="cur" x="{lx + 140}" y="{y - 11}" width="8" height="14" fill="{CYAN}"/></g>')

    # Bottom status rail.
    by = 384
    o.append(f'<circle class="pulse" cx="46" cy="{by - 4}" r="3.5" fill="{CYAN}"/>')
    o.append(text(58, by, "ONLINE", 10, CYAN, spacing=2.5))
    o.append(text(130, by, "agentic ai  ·  llm systems  ·  backend  ·  cloud & devops  ·  ai security",
                  10, MUTED, spacing=1.2))
    o.append(text(W - 40, by, "PUNE / IN", 10, MUTED, anchor="end", spacing=2.5))

    o.append(f'<rect width="{W}" height="{H}" fill="url(#scan)"/>')
    o.append("</g>")
    o.append(f'<polygon points="{chamfer(0.5, 0.5, W - 1, H - 1, 22)}" fill="none" stroke="{LINE_2}"/>')
    o.append(f'<path d="M{W - 70},5 H{W - 30} M{W - 5},30 V70 M5,{H - 70} V{H - 30} M30,{H - 5} H70" '
             f'stroke="{CYAN}" stroke-width="1.5" opacity="0.7"/>')
    o.append("</svg>\n")
    return "\n".join(o)


# --- section headers --------------------------------------------------------
# Transparent, so they sit on GitHub's page in both light and dark mode; the
# colours are mid-tones that read on white and on #0d1117.

HEADERS = [
    ("operator", "01", "OPERATOR PROFILE", "/home/omkar", "#0098B7"),
    ("missions", "02", "MISSION ARCHIVE", "/var/missions", "#D0216F"),
    ("city", "03", "CONTRIBUTION CITY", "/sector/09", "#7C4DEB"),
    ("arsenal", "04", "TECH ARSENAL", "/usr/arsenal", "#0098B7"),
    ("transmission", "05", "TRANSMISSION", "/dev/tty", "#D0216F"),
]


def header(index: str, title: str, path: str, accent: str) -> str:
    # Compact and shown at its natural width, so it stays legible on phones.
    W, H = 560, 60
    o = [svg_open(W, H, f"{index}. {title.title()}")]
    o.append(text(0, 40, index, 30, accent, family=MONO, weight=700))
    o.append(text(52, 38, title, 15, accent, weight=700, spacing=4.5))
    o.append(f'<rect x="52" y="47" width="22" height="3" fill="{accent}"/>')
    # Rail: a hairline with a notch, a few ticks, and the path tag beneath it.
    x1 = 52 + len(title) * 13.6 + 18
    o.append(f'<path d="M{x1:.0f},33 H{x1 + 24:.0f} L{x1 + 32:.0f},27 H{W - 20}" fill="none" '
             f'stroke="#6B7699" stroke-width="1" opacity="0.55"/>')
    for k in range(3):
        o.append(f'<rect x="{W - 14 + k * 5}" y="24" width="2" height="6" fill="{accent}" opacity="{0.4 + k * 0.3:.1f}"/>')
    o.append(text(W, 50, path, 10.5, "#6B7699", anchor="end", spacing=1))
    o.append("</svg>\n")
    return "\n".join(o)


# --- tech arsenal -----------------------------------------------------------
# Only tools that appear in the projects on this profile.

def icon(kind: str, x: float, y: float, c: str) -> str:
    s = f'fill="none" stroke="{c}" stroke-width="1.5"'
    if kind == "agents":   # three nodes, one planner
        return (f'<g {s}><circle cx="{x + 3}" cy="{y + 3}" r="2.6"/><circle cx="{x + 15}" cy="{y + 3}" r="2.6"/>'
                f'<circle cx="{x + 9}" cy="{y + 14}" r="2.6"/><path d="M{x + 5},{y + 5} L{x + 8},{y + 11.5} M{x + 13},{y + 5} L{x + 10},{y + 11.5}"/></g>'
                f'<circle cx="{x + 9}" cy="{y + 14}" r="1.2" fill="{c}"/>')
    if kind == "lang":
        return f'<path {s} d="M{x + 5},{y} L{x},{y + 8.5} L{x + 5},{y + 17} M{x + 13},{y} L{x + 18},{y + 8.5} L{x + 13},{y + 17} M{x + 11},{y + 1} L{x + 7},{y + 16}"/>'
    if kind == "backend":
        return (f'<g {s}><rect x="{x}" y="{y}" width="18" height="6"/><rect x="{x}" y="{y + 10}" width="18" height="6"/></g>'
                f'<rect x="{x + 3}" y="{y + 2}" width="2" height="2" fill="{c}"/><rect x="{x + 3}" y="{y + 12}" width="2" height="2" fill="{c}"/>')
    if kind == "cloud":
        return f'<path {s} d="M{x + 9},{y} L{x + 17},{y + 4.5} V{y + 13.5} L{x + 9},{y + 18} L{x + 1},{y + 13.5} V{y + 4.5} Z M{x + 9},{y + 9} V{y + 18} M{x + 9},{y + 9} L{x + 17},{y + 4.5} M{x + 9},{y + 9} L{x + 1},{y + 4.5}"/>'
    if kind == "data":
        return f'<path {s} d="M{x + 1},{y + 3} C{x + 1},{y - 1} {x + 17},{y - 1} {x + 17},{y + 3} V{y + 14} C{x + 17},{y + 18} {x + 1},{y + 18} {x + 1},{y + 14} Z M{x + 1},{y + 3} C{x + 1},{y + 7} {x + 17},{y + 7} {x + 17},{y + 3} M{x + 1},{y + 9} C{x + 1},{y + 13} {x + 17},{y + 13} {x + 17},{y + 9}"/>'
    if kind == "sec":      # crosshair
        return (f'<g {s}><circle cx="{x + 9}" cy="{y + 9}" r="6.5"/><path d="M{x + 9},{y - 1} V{y + 4} M{x + 9},{y + 14} V{y + 19} '
                f'M{x - 1},{y + 9} H{x + 4} M{x + 14},{y + 9} H{x + 19}"/></g><circle cx="{x + 9}" cy="{y + 9}" r="1.4" fill="{c}"/>')
    raise ValueError(kind)


def arsenal() -> str:
    W, H = 1000, 392
    label = ("Tech arsenal. Agents and LLM systems: custom orchestration loops, LangGraph, structured "
             "JSON outputs with Pydantic, RAG with HyDE, query rewriting and reranking, Gemini, OpenAI, "
             "Groq, OpenRouter. Languages: Python, TypeScript, C++, SQL. Backend: Node.js, Express, REST "
             "APIs, Redis queues, httpx, Playwright. Cloud and DevOps: Docker, Docker Compose, GitHub "
             "Actions, AWS. Data: PostgreSQL, SQLite, Redis, Pinecone. Security tooling: OWASP ZAP, nuclei, "
             "sqlmap, ffuf, nmap, subfinder, katana, dalfox, nikto.")
    o = [svg_open(W, H, label)]
    o.append(f"""<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{INK}"/><stop offset="1" stop-color="#0A0F24"/></linearGradient>
  <radialGradient id="g" cx="0.15" cy="0.3" r="0.5"><stop offset="0" stop-color="#0E3A55" stop-opacity="0.5"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></radialGradient>
</defs>""")
    o.append(f'<polygon points="{chamfer(0, 0, W, H, 18)}" fill="url(#bg)"/>')
    o.append(f'<polygon points="{chamfer(0, 0, W, H, 18)}" fill="url(#g)"/>')
    o.append(f'<polygon points="{chamfer(0.5, 0.5, W - 1, H - 1, 18)}" fill="none" stroke="{LINE_2}"/>')

    # Primary slot: the work the rest of the stack exists to serve.
    px, py, pw, ph = 28, 28, 330, 262
    o.append(f'<polygon points="{chamfer(px, py, pw, ph, 12, "tl")}" fill="#0C1A33" stroke="#164E6B"/>')
    o.append(f'<rect x="{px}" y="{py + 18}" width="3" height="40" fill="{CYAN}"/>')
    o.append(icon("agents", px + 22, py + 22, CYAN))
    o.append(text(px + 52, py + 32, "SLOT 0 · PRIMARY", 10, CYAN, spacing=2.5))
    o.append(text(px + 52, py + 50, "Agents & LLM systems", 17, TEXT, family=SANS, weight=600))
    rows = [
        ("Custom orchestration loops", "no framework where one isn't needed"),
        ("LangGraph", "multi-agent graphs, reviewer loops"),
        ("Structured outputs", "JSON mode + Pydantic validation"),
        ("RAG", "HyDE · query rewriting · reranking"),
        ("Models", "Gemini · OpenAI · Groq · OpenRouter"),
    ]
    for k, (a, b) in enumerate(rows):
        y = py + 92 + k * 34
        o.append(text(px + 22, y, a, 13.5, TEXT, family=SANS))
        o.append(text(px + 22, y + 15, b, 10.5, MUTED))

    # Secondary slots, 2 x 2.
    cells = [
        ("lang", "SLOT 1", "Languages", ["Python", "TypeScript", "C++ (DSA)", "SQL"], PURPLE),
        ("backend", "SLOT 2", "Backend", ["Node.js · Express", "REST APIs", "Redis queues", "httpx · Playwright"], PURPLE),
        ("cloud", "SLOT 3", "Cloud & DevOps", ["Docker · Compose", "GitHub Actions", "AWS: S3 · Lambda · ECS · RDS", "CloudFront · WAF · CloudWatch · SNS"], MAGENTA),
        ("data", "SLOT 4", "Data", ["PostgreSQL (Neon)", "SQLite", "Redis", "Pinecone"], MAGENTA),
    ]
    gx, gy = 380, 28
    colw = [330, 262]
    for k, (ic, slot, title, items, accent) in enumerate(cells):
        cx = gx + (0 if k % 2 == 0 else colw[0] + 0)
        cy = gy + (k // 2) * 136
        w = colw[k % 2]
        o.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + w - 20}" y2="{cy}" stroke="{LINE_2}"/>')
        o.append(f'<rect x="{cx}" y="{cy - 1}" width="18" height="3" fill="{accent}"/>')
        o.append(icon(ic, cx, cy + 16, accent))
        o.append(text(cx + 30, cy + 24, slot, 9.5, accent, spacing=2.5))
        o.append(text(cx + 30, cy + 40, title, 14.5, TEXT, family=SANS, weight=600))
        for n, it in enumerate(items):
            o.append(text(cx + 30, cy + 62 + n * 17, it, 12, "#B4BCDA", family=SANS))

    # Security tooling: a single rail across the bottom.
    sy = 316
    o.append(f'<line x1="28" y1="{sy}" x2="{W - 28}" y2="{sy}" stroke="{LINE_2}"/>')
    o.append(f'<rect x="28" y="{sy - 1}" width="18" height="3" fill="{AMBER}"/>')
    o.append(icon("sec", 28, sy + 18, AMBER))
    o.append(text(58, sy + 26, "SLOT 5 · OFFENSIVE SECURITY TOOLING", 9.5, AMBER, spacing=2.5))
    tools = ["OWASP ZAP", "nuclei", "sqlmap", "ffuf", "nmap", "subfinder", "katana", "dalfox", "nikto"]
    o.append(text(58, sy + 50, "   /   ".join(tools), 12.5, "#B4BCDA"))
    o.append("</svg>\n")
    return "\n".join(o)


# --- transmission channels --------------------------------------------------

CHANNELS = [
    ("portfolio", "CH·01", "PORTFOLIO", "omkarnjoshi.vercel.app", CYAN),
    ("linkedin", "CH·02", "LINKEDIN", "in/omkarjoshi9", PURPLE),
    ("leetcode", "CH·03", "LEETCODE", "u/omkarjoshi2005", PURPLE),
    ("mail", "CH·04", "MAIL", "omkarnjoshi9@gmail.com", MAGENTA),
]


def channel(code: str, name: str, handle: str, accent: str) -> str:
    W, H = 480, 76
    o = [svg_open(W, H, f"{name.title()}: {handle}")]
    o.append(f'<polygon points="{chamfer(0.5, 0.5, W - 1, H - 1, 12)}" fill="{NAVY}" stroke="{LINE_2}"/>')
    o.append(f'<rect x="0.5" y="16" width="3" height="44" fill="{accent}"/>')
    o.append(text(24, 30, code, 10, accent, spacing=2.5))
    o.append(text(24, 54, name, 17, TEXT, weight=700, spacing=4))
    o.append(text(W - 50, 46, handle, 12, MUTED, anchor="end"))
    # outbound arrow
    o.append(f'<path d="M{W - 34},{44} L{W - 24},{34} M{W - 31},{34} H{W - 24} V{41}" fill="none" '
             f'stroke="{accent}" stroke-width="1.6"/>')
    o.append("</svg>\n")
    return "\n".join(o)


def main() -> None:
    write("hero.svg", hero())
    for slug, idx, title, path, accent in HEADERS:
        write(f"headers/{slug}.svg", header(idx, title, path, accent))
    write("arsenal.svg", arsenal())
    for slug, code, name, handle, accent in CHANNELS:
        write(f"channels/{slug}.svg", channel(code, name, handle, accent))


if __name__ == "__main__":
    main()
