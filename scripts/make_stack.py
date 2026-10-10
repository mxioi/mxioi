#!/usr/bin/env python3
"""Build the animated tech stack card (assets/stack-dark.svg and stack-light.svg).

Edit STACK below, then run:
    python scripts/make_stack.py
and commit the two SVGs.

Brand logos come from scripts/icons.json (Simple Icons, CC0). Tools without a
logo there get a simple generic glyph from GLYPHS instead.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
ICONS = json.loads((ROOT / "scripts" / "icons.json").read_text(encoding="utf-8"))

# (column title, accent colour, [(label, icon key from icons.json or GLYPHS, colour override)])
STACK = [
    ("Identity & endpoints", "#3b82f6", [
        ("Active Directory", "tree", "#0078d4"),
        ("SCCM / MECM", "box", "#0078d4"),
        ("Intune", "laptop", "#0078d4"),
        ("Windows Server", "server", "#0078d4"),
        ("PowerShell", "prompt", "#5391fe"),
    ]),
    ("Networking & security", "#06b6d4", [
        ("UniFi", "ubiquiti", None),
        ("pfSense", "pfsense", None),
        ("Cisco", "cisco", None),
        ("RADIUS / 802.1X", "lock", "#14b8a6"),
        ("DNS & NAT", "globe", "#14b8a6"),
    ]),
    ("Linux & self-hosting", "#f97316", [
        ("Proxmox", "proxmox", None),
        ("Docker", "docker", None),
        ("Kubernetes", "kubernetes", None),
        ("Nginx", "nginx", None),
        ("Ubuntu", "ubuntu", None),
        ("Bash", "gnubash", None),
    ]),
    ("Automation & code", "#a855f7", [
        ("Python", "python", None),
        ("n8n", "n8n", None),
        ("Git", "git", None),
        ("GitHub Actions", "githubactions", None),
    ]),
    ("Learning now", "#22c55e", [
        ("Azure cloud", "cloud", "#0078d4"),
        ("DevOps", "loop", "#22c55e"),
    ]),
]

# Generic 24x24 line glyphs for tools without a brand logo.
GLYPHS = {
    "tree": '<rect x="9" y="2" width="6" height="5" rx="1"/><rect x="2" y="17" width="6" height="5" rx="1"/>'
            '<rect x="16" y="17" width="6" height="5" rx="1"/><rect x="9" y="17" width="6" height="5" rx="1"/>'
            '<path d="M12 7v10M5 17v-4h14v4"/>',
    "box": '<path d="M12 2.5l8.5 4.75v9.5L12 21.5l-8.5-4.75v-9.5z"/><path d="M3.5 7.25L12 12l8.5-4.75M12 12v9.5"/>',
    "laptop": '<rect x="4" y="4" width="16" height="11" rx="1.5"/><path d="M2 19h20"/><path d="M10 9.5l1.5 1.5 3-3"/>',
    "server": '<rect x="3" y="3" width="18" height="7" rx="1.5"/><rect x="3" y="14" width="18" height="7" rx="1.5"/>'
              '<path d="M7 6.5h.01M7 17.5h.01M11 6.5h6M11 17.5h6"/>',
    "prompt": '<rect x="2" y="3" width="20" height="18" rx="2.5"/><path d="M6.5 9l4 3-4 3M12.5 16h5"/>',
    "lock": '<rect x="4" y="10.5" width="16" height="11" rx="2"/><path d="M8 10.5V7a4 4 0 0 1 8 0v3.5M12 15v2.5"/>',
    "globe": '<circle cx="12" cy="12" r="9.5"/><path d="M2.5 12h19M12 2.5c3 3.2 3 15.8 0 19M12 2.5c-3 3.2-3 15.8 0 19"/>',
    "cloud": '<path d="M7 19h10.5a4.5 4.5 0 0 0 .6-8.96A6 6 0 0 0 6.6 9.2 5 5 0 0 0 7 19z"/>',
    "loop": '<path d="M8 8.5c-2-2-6-1.2-6 3.5s4 5.5 6 3.5l8-7c2-2 6-1.2 6 3.5s-4 5.5-6 3.5z"/>',
}

THEMES = {
    "dark": dict(bg1="#0d1117", bg2="#161b2e", card="#161b22", border="#30363d", text="#e6edf3",
                 muted="#8b949e", chip="#0d1117"),
    "light": dict(bg1="#ffffff", bg2="#eef4ff", card="#ffffff", border="#d0d7de", text="#1f2328",
                  muted="#57606a", chip="#f6f8fa"),
}
SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SFMono-Regular', 'Cascadia Code', Consolas, 'Liberation Mono', monospace"

W = 840
PAD = 22
GAP = 18
ROWS = [2, 2, 1]       # cards per row; the cards in STACK fill these rows in order
HEAD_H = 62            # space for the card title
CHIP_H = 44
CHIP_GAP = 10
CHAR_W = 10.2          # rough width of one label character at 18px (semibold)


def layout():
    """Place cards in rows and flow each card's chips left to right, wrapping as needed."""
    cards, y, i = [], PAD, 0
    for n in ROWS:
        row = STACK[i:i + n]
        i += n
        cw = (W - 2 * PAD - GAP * (n - 1)) / n
        placed = []
        for ci, (title, accent, items) in enumerate(row):
            x = PAD + ci * (cw + GAP)
            cx, cy, chips = x + 16, y + HEAD_H, []
            for label, key, colour in items:
                w = 58 + len(label) * CHAR_W + sum(c.isupper() for c in label) * 2.5
                if cx + w > x + cw - 16 and cx > x + 16:
                    cx, cy = x + 16, cy + CHIP_H + CHIP_GAP
                chips.append((cx, cy, w, label, key, colour))
                cx += w + CHIP_GAP
            placed.append([x, cw, title, accent, chips, cy + CHIP_H + 18 - y])
        h = max(c[5] for c in placed)
        for c in placed:
            cards.append((c[0], y, c[1], h, c[2], c[3], c[4]))
        y += h + GAP
    return cards, y - GAP + PAD

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def icon(key, colour, dark):
    if key in ICONS:
        hex_ = colour or "#" + ICONS[key]["hex"]
        # A few brand colours are near-black; lift them in dark mode so they stay visible.
        if dark and hex_.lower() in ("#000000", "#212121", "#181717", "#1d1d1d", "#2088ff"):
            hex_ = "#e6edf3" if hex_.lower() != "#2088ff" else hex_
        return f'<path d="{ICONS[key]["path"]}" fill="{hex_}"/>'
    return (f'<g fill="none" stroke="{colour}" stroke-width="2" stroke-linecap="round" '
            f'stroke-linejoin="round">{GLYPHS[key]}</g>')


def svg(theme):
    c = THEMES[theme]
    cards, H = layout()
    parts = []
    for ci, (x, y, cw, h, title, accent, chips) in enumerate(cards):
        parts.append(f'<g class="col" style="animation-delay:{ci * 0.12:.2f}s">')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="{h}" rx="16" class="card"/>')
        parts.append(f'<rect x="{x:.1f}" y="{y}" width="{cw:.1f}" height="5" rx="2.5" fill="{accent}"/>')
        parts.append(f'<text x="{x + 18:.1f}" y="{y + 40}" class="head" fill="{accent}">{esc(title)}</text>')
        parts.append('</g>')
        for ri, (ix, iy, w, label, key, colour) in enumerate(chips):
            delay = 0.25 + ci * 0.12 + ri * 0.07
            parts.append(f'<g class="item" style="animation-delay:{delay:.2f}s">')
            parts.append(f'<rect x="{ix:.1f}" y="{iy}" width="{w:.1f}" height="{CHIP_H}" rx="10" class="chip"/>')
            beat = 2.5 + ci * 0.2 + ri * 0.3  # when the glow reaches this chip
            parts.append(f'<rect x="{ix:.1f}" y="{iy}" width="{w:.1f}" height="{CHIP_H}" rx="10" fill="none" '
                         f'stroke="{accent}" stroke-width="2" class="glow" '
                         f'style="animation-delay:{beat:.2f}s"/>')
            parts.append(f'<g transform="translate({ix + 12:.1f} {iy + 11})"><g class="logo" '
                         f'style="animation-delay:{delay + 0.15:.2f}s,{beat:.2f}s">'
                         f'{icon(key, colour, theme == "dark")}</g></g>')
            parts.append(f'<text x="{ix + 46:.1f}" y="{iy + 28.5}" class="lbl">{esc(label)}</text>')
            parts.append('</g>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Tech stack: {esc(", ".join(label for _, _, items in STACK for label, _, _ in items))}</title>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/></linearGradient>
</defs>
<style>
.card{{fill:{c['card']};stroke:{c['border']};stroke-width:1}}
.chip{{fill:{c['chip']};stroke:{c['border']};stroke-width:1}}
.head{{font:700 20px {SANS};letter-spacing:.2px}}
.lbl{{font:600 18px {SANS};fill:{c['text']}}}
.col{{animation:rise .6s cubic-bezier(.2,.7,.2,1) both}}
.item{{animation:pop .5s ease-out both}}
.glow{{opacity:0;animation:glow 9s ease-in-out infinite}}
.logo{{transform-box:fill-box;transform-origin:center;animation:logo-in .6s cubic-bezier(.3,1.6,.5,1) both,logo-beat 9s ease-in-out infinite}}
@keyframes rise{{from{{opacity:0;transform:translateY(14px)}}to{{opacity:1;transform:none}}}}
@keyframes pop{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
@keyframes glow{{0%,14%,100%{{opacity:0}}5%{{opacity:.85}}}}
@keyframes logo-in{{from{{opacity:0;transform:scale(.4) rotate(-20deg)}}to{{opacity:1;transform:none}}}}
@keyframes logo-beat{{0%,12%,100%{{transform:none}}4%{{transform:translateY(-3px) scale(1.18)}}8%{{transform:translateY(0) scale(.97)}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
</style>
<rect width="{W}" height="{H}" rx="18" fill="url(#bg)"/>
{chr(10).join(parts)}
</svg>
'''


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for t in THEMES:
        (OUT / f"stack-{t}.svg").write_text(svg(t), encoding="utf-8")
    print("wrote assets/stack-dark.svg and assets/stack-light.svg")
