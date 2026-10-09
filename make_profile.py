#!/usr/bin/env python3
"""Genera dark_mode.svg y light_mode.svg (tarjeta estilo neofetch) a partir de
ascii_art.txt + data.json + las filas fijas definidas abajo. Solo stdlib."""
import datetime
import json
from xml.sax.saxutils import escape

USER = "odemaria"
QA_SINCE = 2016

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", art="#8b949e", title="#7ee787", key="#58a6ff",
                 text="#c9d1d9", muted="#8b949e", star="#e3b341"),
    "light": dict(bg="#ffffff", border="#d0d7de", art="#6e7781", title="#1a7f37", key="#0969da",
                  text="#1f2328", muted="#656d76", star="#9a6700"),
}

PAD = 24
ROW_FONT, ROW_LH, GAP = 13.5, 22.0, 11.0
# ancho por caracter estimado con la fuente mas ancha del stack (DejaVu ~0.60em)
ROW_CW = 0.61 * ROW_FONT
# el arte braille se dibuja punto a punto: ninguna fuente comun trae braille de ancho
# fijo, y como texto el dibujo sale chueco segun el sistema
DOT_STEP, DOT_R = 4.0, 1.35
DOTS = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]


def rows(d):
    """Cada fila: None (separador) o (clave, [(texto, color), ...])."""
    years = datetime.date.today().year - QA_SINCE
    t = lambda s: [(s, "text")]
    stars = f"{d['stars']} star" + ("" if d["stars"] == "1" else "s")
    return [
        ("Host", t("Santiago, Chile")),
        ("Role", t("QA Lead · QA Automation Engineer")),
        ("Uptime", t(f"{years}+ years in QA (since {QA_SINCE})")),
        ("Focus", t("Test strategy · E2E/API automation · Performance")),
        None,
        ("Languages.Programming", t("Python, Java, TypeScript, JavaScript")),
        ("Languages.Real", t("Español, English")),
        None,
        ("Testing.E2E", t("Selenium · Cypress · Playwright")),
        ("Testing.API", t("Postman/Newman · RestAssured · Karate")),
        ("Testing.Performance", t("k6 · JMeter")),
        ("DevOps", t("Docker · GitHub Actions · Jenkins")),
        ("AI", t("Claude Code · GitHub Copilot · Codex")),
        ("Certs", t("ISTQB CTFL · Scrum Master (SFPC)")),
        None,
        ("Contact.LinkedIn", t("in/omardemaria")),
        None,
        ("Stats.Repos", [(f"{d['repos']}  ·  ", "text"), (stars, "star"),
                         (f"  ·  {d['followers']} followers", "text")]),
        ("Stats.Commits", t(d["commits"])),
    ]


def art_paths(art, top):
    """Un <path> por linea braille: cada punto encendido es un circulo."""
    paths = []
    for row, line in enumerate(art):
        d = []
        for col, ch in enumerate(line):
            bits = ord(ch) - 0x2800
            if not 0 < bits <= 0xFF:
                continue
            for dy in range(4):
                for dx in range(2):
                    if bits & DOTS[dy][dx]:
                        cx = PAD + (col * 2 + dx + 0.5) * DOT_STEP
                        cy = top + (row * 4 + dy + 0.5) * DOT_STEP
                        d.append(f"M{cx - DOT_R:.2f} {cy:.2f}a{DOT_R} {DOT_R} 0 1 0 {2 * DOT_R} 0"
                                 f"a{DOT_R} {DOT_R} 0 1 0 {-2 * DOT_R} 0")
        if d:
            paths.append(f'<path class="art" style="animation-delay:{row * 0.02:.2f}s" d="{"".join(d)}"/>')
    return "\n".join(paths)


def build(theme, art, data):
    c = THEMES[theme]
    art_w = max(len(l) for l in art) * 2 * DOT_STEP
    art_h = len(art) * 4 * DOT_STEP
    x = PAD + art_w + 36
    title = f"{USER}@github"

    out, y, delay = [], PAD + 13.5, 0.5

    def row(spans):
        nonlocal y, delay
        bold = lambda col: ' font-weight="bold"' if col in ("key", "title") else ""
        tspans = "".join(f'<tspan fill="{c[col]}"{bold(col)}>{escape(txt)}</tspan>' for txt, col in spans)
        out.append(f'<text class="row" x="{x:.1f}" y="{y:.1f}" font-size="{ROW_FONT}" xml:space="preserve" '
                   f'style="animation-delay:{delay:.2f}s">{tspans}</text>')
        y += ROW_LH
        delay += 0.12

    row([(USER, "title"), ("@github", "muted")])
    row([("-" * len(title), "muted")])
    longest = len(title)
    for r in rows(data):
        if r is None:
            y += GAP
            continue
        key, val = r
        row([(key, "key"), (": ", "muted")] + val)
        longest = max(longest, len(key) + 2 + sum(len(s) for s, _ in val))
    cursor_y, cursor_delay = y, delay

    width = int(x + longest * ROW_CW + PAD)
    height = int(max(cursor_y + PAD, PAD * 2 + art_h))

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Consolas, 'DejaVu Sans Mono', Menlo, 'Courier New', monospace">
<style>@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}}@keyframes blink{{50%{{opacity:0}}}}.art{{fill:{c['art']};animation:fade .3s ease backwards}}.row{{animation:fade .15s ease backwards}}</style>
<rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="10" fill="{c['bg']}" stroke="{c['border']}" stroke-width="1.5"/>
{art_paths(art, (height - art_h) / 2)}
{chr(10).join(out)}
<text x="{x:.1f}" y="{cursor_y:.1f}" font-size="{ROW_FONT}" fill="{c['title']}" style="animation:fade .01s backwards {cursor_delay:.2f}s, blink 1.1s steps(1) {cursor_delay + 0.3:.2f}s infinite">&#9611;</text>
</svg>
"""


if __name__ == "__main__":
    with open("ascii_art.txt", encoding="utf-8") as f:
        art = f.read().rstrip("\n").split("\n")
    with open("data.json", encoding="utf-8") as f:
        data = json.load(f)
    for theme in THEMES:
        with open(f"{theme}_mode.svg", "w", encoding="utf-8") as f:
            f.write(build(theme, art, data))
    print("ok: dark_mode.svg, light_mode.svg")
