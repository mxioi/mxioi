#!/usr/bin/env python3
"""Rebuild the projects section of README.md from projects.toml.

Reads the repo list from projects.toml, looks each repo up on the GitHub API
(description, stars, language, visibility) and rewrites everything between the
PROJECTS:START and PROJECTS:END markers in README.md.

Usage:
    GITHUB_TOKEN=... python scripts/update_projects.py
    python scripts/update_projects.py --offline   # use projects.toml only
"""

import json
import os
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER = "mxioi"
ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "projects.toml"
README = ROOT / "README.md"
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"

# Badge colour and simple-icons logo for known tech names. Anything not listed
# still gets a plain grey badge.
BADGES = {
    "Active Directory": ("0078D4", "microsoft"),
    "Bash": ("4EAA25", "gnubash"),
    "CadQuery": ("1F6FEB", "python"),
    "CUDA": ("76B900", "nvidia"),
    "Docker": ("2496ED", "docker"),
    "FastAPI": ("009688", "fastapi"),
    "FFmpeg": ("007808", "ffmpeg"),
    "Kubernetes": ("326CE5", "kubernetes"),
    "Linux": ("FCC624", "linux"),
    "Networking": ("1BA0D7", "cisco"),
    "Plex": ("E5A00D", "plex"),
    "PowerShell": ("5391FE", "powershell"),
    "Python": ("3776AB", "python"),
    "SCCM": ("0078D4", "microsoft"),
    "UniFi": ("0559C9", "ubiquiti"),
    "Vulkan": ("AC162C", "vulkan"),
    "Whisper": ("412991", "openai"),
    "Wine": ("800000", "wine"),
}

DARK_TEXT = {"FCC624"}


def badge(name, style):
    colour, logo = BADGES.get(name, ("555555", ""))
    label = urllib.parse.quote(name.replace("-", "--").replace("_", "__"))
    logo_colour = "black" if colour in DARK_TEXT else "white"
    url = f"https://img.shields.io/badge/{label}-{colour}?style={style}"
    if logo:
        url += f"&logo={logo}&logoColor={logo_colour}"
    return f"![{name}]({url})"


def fetch_repo(name, token):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{USER}/{name}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER},
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def resolve(entries, offline, token):
    """Merge config with live repo data, dropping repos that aren't public."""
    projects = []
    for entry in entries:
        name = entry["repo"]
        live = {} if offline else fetch_repo(name, token)
        if live is None or live.get("private") or live.get("archived"):
            print(f"skipping {name}: not public", file=sys.stderr)
            continue
        projects.append({
            "url": live.get("html_url", f"https://github.com/{USER}/{name}"),
            "title": entry.get("title", name),
            "emoji": entry.get("emoji", "📦"),
            "summary": entry.get("summary") or live.get("description") or "",
            "shows": entry.get("shows", ""),
            "tech": entry.get("tech") or ([live["language"]] if live.get("language") else []),
            "stars": live.get("stargazers_count", 0),
        })
    return projects


def render_card(p):
    stars = f" · ⭐ {p['stars']}" if p["stars"] else ""
    lines = [
        '<td width="50%" valign="top">',
        "",
        f"### {p['emoji']} [{p['title']}]({p['url']})",
    ]
    if p["summary"]:
        lines.append(f"**{p['summary']}**{stars}")
    if p["shows"]:
        lines += ["", p["shows"]]
    if p["tech"]:
        lines += ["", " ".join(badge(t, "flat-square") for t in p["tech"])]
    lines += ["", "</td>"]
    return lines


def render(featured, more):
    out = [START, "<!-- Generated from projects.toml by scripts/update_projects.py. Edit that file, not this section. -->", ""]
    if featured:
        out.append("<table>")
        for i in range(0, len(featured), 2):
            out.append("<tr>")
            for p in featured[i:i + 2]:
                out += render_card(p)
            out.append("</tr>")
        out += ["</table>", ""]
    if more:
        out += [
            "<details>",
            "<summary><b>📂 More projects</b></summary>",
            "<br/>",
            "",
            "| Project | Description | Tech |",
            "|:--------|:------------|:-----|",
        ]
        for p in more:
            tech = " ".join(badge(t, "flat-square") for t in p["tech"])
            out.append(f"| [{p['title']}]({p['url']}) | {p['summary']} | {tech} |")
        out += ["", "</details>", ""]
    out.append(END)
    return "\n".join(out)


def main():
    offline = "--offline" in sys.argv
    token = os.environ.get("GITHUB_TOKEN")
    config = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    featured = resolve(config.get("featured", []), offline, token)
    more = resolve(config.get("more", []), offline, token)

    readme = README.read_text(encoding="utf-8")
    if START not in readme or END not in readme:
        sys.exit(f"README.md is missing the {START} / {END} markers")
    before, rest = readme.split(START, 1)
    _, after = rest.split(END, 1)
    README.write_text(before + render(featured, more) + after, encoding="utf-8")
    print(f"wrote {len(featured)} featured and {len(more)} more projects")


if __name__ == "__main__":
    main()
