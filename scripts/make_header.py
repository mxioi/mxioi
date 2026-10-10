#!/usr/bin/env python3
"""Build the animated profile header (assets/header-dark.svg and header-light.svg).

Edit LINES (the rotating taglines) or NODES (the little network diagram), then run:
    python scripts/make_header.py
and commit the two SVGs. GitHub picks the dark or light one to match the viewer's theme.
"""

from pathlib import Path

out = Path(__file__).resolve().parent.parent / "assets"
out.mkdir(exist_ok=True)

THEMES = {
  "dark": dict(bg1="#0d1117", bg2="#161b2e", dot="#30363d", text="#e6edf3", muted="#8b949e",
               accent="#58a6ff", accent2="#a371f7", node="#161b22", stroke="#30363d", ok="#3fb950", line="#30363d"),
  "light": dict(bg1="#ffffff", bg2="#eef4ff", dot="#d0d7de", text="#1f2328", muted="#57606a",
               accent="#0969da", accent2="#8250df", node="#ffffff", stroke="#d0d7de", ok="#1a7f37", line="#c8d1da"),
}
SANS = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "ui-monospace, 'SFMono-Regular', 'Cascadia Code', Consolas, 'Liberation Mono', monospace"

LINES = ["Windows &amp; Linux infrastructure",
         "Active Directory · SCCM/MECM · Intune",
         "UniFi · pfSense · RADIUS/802.1X",
         "Proxmox · Docker · homelab automation"]

# topology nodes: id -> (x, y, label, sub)
NODES = {
  "wan": (816, 58, "internet", ""),
  "fw":  (816, 145, "pfSense", "fw-01"),
  "sw":  (816, 232, "UniFi", "core-sw"),
  "dc":  (712, 332, "AD DS", "dc-01"),
  "pve": (816, 332, "Proxmox", "pve-01"),
  "k8s": (920, 332, "Docker", "k3s-01"),
}
EDGES = [("wan","fw"),("fw","sw"),("sw","dc"),("sw","pve"),("sw","k8s")]
W, H = 96, 46

def edge_path(a, b):
    ax, ay = NODES[a][:2]; bx, by = NODES[b][:2]
    y1, y2 = ay + H/2, by - H/2
    if ax == bx:
        return f"M{ax} {y1} V{y2}"
    my = (y1 + y2) / 2
    return f"M{ax} {y1} V{my} H{bx} V{y2}"

def svg(t):
    c = THEMES[t]
    n = len(LINES); per = 3.5; total = per * n
    keyframes = []
    for i in range(n):
        s = i / n * 100; e = (i + 1) / n * 100
        keyframes.append(f""".l{i}{{animation:l{i} {total}s infinite}}
@keyframes l{i}{{0%{{opacity:0}}{max(s,0):.2f}%{{opacity:0}}{s+1.5:.2f}%{{opacity:1}}{e-1.5:.2f}%{{opacity:1}}{e:.2f}%{{opacity:0}}100%{{opacity:0}}}}""")
    edges = []; packets = []
    for i, (a, b) in enumerate(EDGES):
        d = edge_path(a, b)
        edges.append(f'<path id="e{i}" d="{d}" class="edge"/>')
        dur = 2.2 + (i % 3) * 0.4
        packets.append(f'<circle r="4.2" class="pkt"><animateMotion dur="{dur}s" begin="{i*0.45:.2f}s" repeatCount="indefinite" keyPoints="0;1" keyTimes="0;1" calcMode="linear"><mpath href="#e{i}"/></animateMotion></circle>')
        packets.append(f'<circle r="3.4" class="pkt2"><animateMotion dur="{dur+0.6}s" begin="{i*0.3+1:.2f}s" repeatCount="indefinite" keyPoints="1;0" keyTimes="0;1" calcMode="linear"><mpath href="#e{i}"/></animateMotion></circle>')
    nodes = []
    for k, (x, y, label, sub) in NODES.items():
        if k == "wan":
            nodes.append(f'<g transform="translate({x} {y})"><rect x="-{W/2}" y="-{H/2}" width="{W}" height="{H}" rx="20" class="node wan"/>'
                         f'<text y="6" class="nl" text-anchor="middle">{label}</text></g>')
            continue
        delay = list(NODES).index(k) * 0.4
        nodes.append(f'<g transform="translate({x} {y})"><rect x="-{W/2}" y="-{H/2}" width="{W}" height="{H}" rx="8" class="node"/>'
                     f'<circle cx="-{W/2-11}" cy="-7" r="4.5" class="led" style="animation-delay:{delay}s"/>'
                     f'<text x="-{W/2-22}" y="-2" class="nl">{label}</text>'
                     f'<text x="-{W/2-22}" y="15" class="ns">{sub}</text></g>')
    lines = "\n".join(
        f'<text x="48" y="336" class="mono rot l{i}"><tspan class="acc">&gt;</tspan> {s}<tspan class="cur">▍</tspan></text>'
        for i, s in enumerate(LINES))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="980" height="400" viewBox="0 0 980 400" role="img" aria-labelledby="title desc">
<title id="title">Michael V</title>
<desc id="desc">Systems Administrator in the UK. Windows and Linux infrastructure, Active Directory, SCCM, Intune, networking and homelab automation.</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['bg1']}"/><stop offset="1" stop-color="{c['bg2']}"/></linearGradient>
<linearGradient id="name" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{c['accent']}"/><stop offset="1" stop-color="{c['accent2']}"/></linearGradient>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="2" cy="2" r="1.2" fill="{c['dot']}"/></pattern>
<linearGradient id="fade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".55" stop-color="#fff" stop-opacity=".15"/><stop offset="1" stop-color="#fff" stop-opacity=".9"/></linearGradient>
<clipPath id="clip"><rect width="980" height="400" rx="18"/></clipPath>
<mask id="m"><rect width="980" height="400" fill="url(#fade)"/></mask>
</defs>
<style>
.sans{{font-family:{SANS}}}
.mono,.nl,.ns{{font-family:{MONO}}}
.name{{font:700 118px {SANS};fill:url(#name)}}
.role{{font:500 38px {SANS};fill:{c['text']}}}
.prompt{{font:24px {MONO};fill:{c['muted']}}}
.rot{{font-size:24px;fill:{c['text']};opacity:0}}
.acc{{fill:{c['accent']}}}
.cur{{fill:{c['accent']};animation:blink 1s steps(1) infinite}}
.edge{{fill:none;stroke:{c['line']};stroke-width:2}}
.pkt{{fill:{c['accent']}}}
.pkt2{{fill:{c['accent2']}}}
.node{{fill:{c['node']};stroke:{c['stroke']};stroke-width:1.5}}
.wan{{stroke:{c['accent']};stroke-dasharray:4 4}}
.nl{{font-size:15px;font-weight:600;fill:{c['text']}}}
.ns{{font-size:12.5px;fill:{c['muted']}}}
.led{{fill:{c['ok']};animation:led 2.4s ease-in-out infinite}}
.bar{{fill:url(#name)}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes led{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
{chr(10).join(keyframes)}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}}.l0{{opacity:1}}.pkt,.pkt2{{display:none}}}}
</style>
<g clip-path="url(#clip)">
<rect width="980" height="400" fill="url(#bg)"/>
<rect width="980" height="400" fill="url(#dots)" mask="url(#m)"/>
<rect x="0" y="0" width="980" height="5" class="bar"/>
</g>
<text x="48" y="92" class="prompt"><tspan class="acc">michael@homelab</tspan>:~$ whoami</text>
<text x="42" y="206" class="name">Michael V</text>
<text x="48" y="268" class="role">Systems Administrator <tspan fill="{c['muted']}">·</tspan> UK</text>
{lines}
<g>
{chr(10).join(edges)}
{chr(10).join(packets)}
{chr(10).join(nodes)}
</g>
</svg>
'''

for t in THEMES:
    (out / f"header-{t}.svg").write_text(svg(t), encoding="utf-8")
