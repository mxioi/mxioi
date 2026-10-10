#!/usr/bin/env python3
"""Build the animated GitHub stats and top-languages cards.

Writes assets/stats-{dark,light}.svg and assets/languages-{dark,light}.svg from
live GitHub data. The "Update stats" workflow runs this weekly, so the cards are
served from this repo and never depend on an outside stats service.

Usage:
    GITHUB_TOKEN=... python scripts/make_stats.py
    python scripts/make_stats.py --sample   # fake numbers, for previewing the design
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

USER = "mxioi"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

# Languages to leave out of the chart (e.g. generated or markup-only code).
EXCLUDE = {"Jupyter Notebook"}
TOP_N = 6

QUERY = """
query($login: String!) {
  user(login: $login) {
    pullRequests { totalCount }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      totalCount
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
  }
}
"""

THEMES = {
    "dark": dict(bg1="#0d1117", bg2="#161b2e", border="#30363d", text="#e6edf3", muted="#8b949e",
                 accent="#58a6ff", accent2="#a371f7", track="#21262d", grid="#21262d"),
    "light": dict(bg1="#ffffff", bg2="#eef4ff", border="#d0d7de", text="#1f2328", muted="#57606a",
                  accent="#0969da", accent2="#8250df", track="#eaeef2", grid="#eaeef2"),
}
SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
W, H = 590, 250

ICONS = {
    "star": '<path d="M12 2.8l2.8 5.7 6.3.9-4.55 4.43 1.07 6.27L12 17.13 6.38 20.1l1.07-6.27L2.9 9.4l6.3-.9z"/>',
    "commit": '<circle cx="12" cy="12" r="3.6"/><path d="M2.5 12h5.9M15.6 12h5.9"/>',
    "pr": '<circle cx="6" cy="5.5" r="2.3"/><circle cx="6" cy="18.5" r="2.3"/><circle cx="18" cy="18.5" r="2.3"/>'
          '<path d="M6 7.8v8.4M18 16.2V9.5a3 3 0 0 0-3-3h-4M13 4l-2.3 2.5L13 9"/>',
    "repo": '<path d="M5 3.5h12.5a1 1 0 0 1 1 1V18H6.5A1.5 1.5 0 0 0 5 19.5zM5 19.5A1.5 1.5 0 0 0 6.5 21h12V18"/>',
    "cal": '<rect x="3" y="4.5" width="18" height="16" rx="2"/><path d="M3 9.5h18M8 2.5v4M16 2.5v4"/>',
}


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": USER})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def sample():
    import random
    rnd = random.Random(1)
    weeks = [{"contributionDays": [{"contributionCount": rnd.randint(0, 6)} for _ in range(7)]} for _ in range(52)]
    langs = [("Python", "#3572A5", 420000), ("PowerShell", "#012456", 160000), ("Shell", "#89e051", 90000),
             ("HTML", "#e34c26", 60000), ("JavaScript", "#f1e05a", 40000), ("Dockerfile", "#384d54", 8000)]
    return {
        "pullRequests": {"totalCount": 12},
        "repositories": {"totalCount": 20, "nodes": [
            {"stargazerCount": 3, "languages": {"edges": [{"size": s, "node": {"name": n, "color": c}} for n, c, s in langs]}}]},
        "contributionsCollection": {"totalCommitContributions": 240, "restrictedContributionsCount": 0,
                                    "contributionCalendar": {"totalContributions": 310, "weeks": weeks}},
    }


def summarise(u):
    repos = u["repositories"]["nodes"]
    cc = u["contributionsCollection"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            name = e["node"]["name"]
            if name in EXCLUDE:
                continue
            size, colour = langs.get(name, (0, e["node"]["color"] or "#8b949e"))
            langs[name] = (size + e["size"], colour)
    total = sum(s for s, _ in langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1][0])[:TOP_N]
    weekly = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in cc["contributionCalendar"]["weeks"]]
    return {
        "stats": [
            ("star", "Stars earned", sum(r["stargazerCount"] for r in repos)),
            ("commit", "Commits, last 12 months", cc["totalCommitContributions"] + cc["restrictedContributionsCount"]),
            ("pr", "Pull requests", u["pullRequests"]["totalCount"]),
            ("repo", "Public repositories", u["repositories"]["totalCount"]),
            ("cal", "Contributions, last 12 months", cc["contributionCalendar"]["totalContributions"]),
        ],
        "langs": [(n, c, s / total * 100) for n, (s, c) in top],
        "weekly": weekly,
    }


def frame(c, title, body, extra_css=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">{title}</title>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/></linearGradient>
<linearGradient id="acc" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c['accent']}"/><stop offset="1" stop-color="{c['accent2']}"/></linearGradient>
<linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c['accent']}" stop-opacity=".35"/><stop offset="1" stop-color="{c['accent']}" stop-opacity="0"/></linearGradient>
</defs>
<style>
.h{{font:700 17px {SANS};fill:{c['text']}}}
.lbl{{font:400 13.5px {SANS};fill:{c['muted']}}}
.val{{font:700 15px {SANS};fill:{c['text']}}}
.fade{{animation:fade .6s ease-out both}}
@keyframes fade{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
{extra_css}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
</style>
<rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="16" fill="url(#bg)" stroke="{c['border']}"/>
<rect x="24" y="24" width="4" height="20" rx="2" fill="url(#acc)"/>
<text x="38" y="40" class="h">{title}</text>
{body}
</svg>
'''


def stats_svg(theme, data):
    c = THEMES[theme]
    rows = []
    for i, (ico, label, value) in enumerate(data["stats"]):
        y = 74 + i * 34
        rows.append(f'<g class="fade" style="animation-delay:{0.15 + i * 0.1:.2f}s">'
                    f'<g transform="translate(26 {y - 14}) scale(.75)" fill="none" stroke="{c["accent"]}" stroke-width="2" '
                    f'stroke-linecap="round" stroke-linejoin="round">{ICONS[ico]}</g>'
                    f'<text x="52" y="{y}" class="lbl">{label}</text>'
                    f'<text x="300" y="{y}" class="val" text-anchor="end">{value:,}</text></g>')

    # Weekly activity sparkline, drawn on with a stroke animation.
    weekly = data["weekly"][-52:] or [0]
    x0, x1, y0, y1 = 330, W - 26, 70, 214
    peak = max(weekly) or 1
    step = (x1 - x0) / max(len(weekly) - 1, 1)
    pts = [(x0 + i * step, y1 - (v / peak) * (y1 - y0)) for i, v in enumerate(weekly)]
    line = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    area = line + f" L{x1:.1f} {y1} L{x0} {y1} Z"
    grid = "".join(f'<path d="M{x0} {y0 + k * (y1 - y0) / 3:.1f}H{x1}" stroke="{c["grid"]}"/>' for k in range(4))
    chart = (f'{grid}<path d="{area}" fill="url(#area)" class="area"/>'
             f'<path d="{line}" fill="none" stroke="url(#acc)" stroke-width="2.2" stroke-linejoin="round" '
             f'stroke-linecap="round" pathLength="1" class="draw"/>'
             f'<circle cx="{pts[-1][0]:.1f}" cy="{pts[-1][1]:.1f}" r="4" fill="{c["accent2"]}" class="dot"/>'
             f'<text x="{x0}" y="{y1 + 22}" class="lbl" style="font-size:12px">Weekly activity, last 12 months</text>')
    css = (".draw{stroke-dasharray:1;stroke-dashoffset:1;animation:draw 2.2s .3s ease-out forwards}"
           "@keyframes draw{to{stroke-dashoffset:0}}"
           ".area{opacity:0;animation:fade 1s 1.6s ease-out forwards}"
           ".dot{opacity:0;animation:pulse 2s 2.4s ease-in-out infinite}"
           "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}")
    return frame(c, "GitHub stats", "\n".join(rows) + chart, css)


def visible(colour, theme):
    """Lighten very dark language colours (e.g. PowerShell's navy) on the dark card."""
    r, g, b = (int(colour.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))
    if theme == "dark" and 0.2126 * r + 0.7152 * g + 0.0722 * b < 70:
        r, g, b = (int(v + (255 - v) * 0.45) for v in (r, g, b))
    return f"#{r:02x}{g:02x}{b:02x}"


def langs_svg(theme, data):
    c = THEMES[theme]
    langs = [(n, visible(col, theme), p) for n, col, p in data["langs"]]
    x0, bw, by = 26, W - 52, 66
    segs, legend = [], []
    x = x0
    for i, (name, colour, pct) in enumerate(langs):
        w = bw * pct / sum(p for _, _, p in langs)
        segs.append(f'<rect x="{x:.1f}" y="{by}" width="{w:.1f}" height="12" fill="{colour}"/>')
        x += w
        col, row = i % 2, i // 2
        lx, ly = 26 + col * 280, 122 + row * 40
        legend.append(f'<g class="fade" style="animation-delay:{0.9 + i * 0.1:.2f}s">'
                      f'<circle cx="{lx + 6}" cy="{ly - 5}" r="6" fill="{colour}"/>'
                      f'<text x="{lx + 20}" y="{ly}" class="val" style="font-weight:600">{name}</text>'
                      f'<text x="{lx + 262}" y="{ly}" class="lbl" text-anchor="end">{pct:.1f}%</text>'
                      f'<rect x="{lx + 20}" y="{ly + 8}" width="242" height="4" rx="2" fill="{c["track"]}"/>'
                      f'<rect x="{lx + 20}" y="{ly + 8}" width="{max(242 * pct / 100, 3):.1f}" height="4" rx="2" '
                      f'fill="{colour}" class="grow" style="animation-delay:{1.1 + i * 0.1:.2f}s"/></g>')
    body = (f'<clipPath id="bar"><rect x="{x0}" y="{by}" width="{bw}" height="12" rx="6"/></clipPath>'
            f'<rect x="{x0}" y="{by}" width="{bw}" height="12" rx="6" fill="{c["track"]}"/>'
            f'<g clip-path="url(#bar)"><g class="wipe">{"".join(segs)}</g></g>' + "\n".join(legend))
    css = (f".wipe{{clip-path:inset(0 100% 0 0);animation:wipe 1.2s .2s cubic-bezier(.2,.7,.2,1) forwards}}"
           "@keyframes wipe{to{clip-path:inset(0 0 0 0)}}"
           ".grow{transform-box:fill-box;transform-origin:left;animation:grow .9s cubic-bezier(.2,.7,.2,1) both}"
           "@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}")
    return frame(c, "Most used languages", body, css)


def main():
    if "--sample" in sys.argv:
        user = sample()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            sys.exit("Set GITHUB_TOKEN (or pass --sample)")
        user = fetch(token)
    data = summarise(user)
    OUT.mkdir(exist_ok=True)
    for t in THEMES:
        (OUT / f"stats-{t}.svg").write_text(stats_svg(t, data), encoding="utf-8")
        (OUT / f"languages-{t}.svg").write_text(langs_svg(t, data), encoding="utf-8")
    print("stats:", {label: v for _, label, v in data["stats"]})
    print("languages:", [(n, round(p, 1)) for n, _, p in data["langs"]])


if __name__ == "__main__":
    main()
