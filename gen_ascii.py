#!/usr/bin/env python3
"""Genera ascii_art.txt: iniciales en braille (contorno solido + relleno tramado).
Solo se corre en local cuando se quiere cambiar el arte; requiere Pillow.

    python gen_ascii.py [TEXTO] [FUENTE.ttf]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

TEXT = sys.argv[1] if len(sys.argv) > 1 else "OD"
FONT = sys.argv[2] if len(sys.argv) > 2 else "C:/Windows/Fonts/arialbd.ttf"
COLS, ROWS = 46, 25          # caracteres braille (cada uno = 2x4 puntos)
W, H = COLS * 2, ROWS * 4    # resolucion final en puntos
SCALE = 8                    # supersampling para un contorno limpio

# bit de cada punto dentro de la celda braille, indexado [y][x]
DOTS = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]


def render_mask():
    big = Image.new("L", (W * SCALE, H * SCALE), 0)
    d = ImageDraw.Draw(big)
    size = H * SCALE
    font = ImageFont.truetype(FONT, size)
    # anillo exterior: los puntos braille son ~cuadrados, asi que un circulo se ve circulo
    diam = min(W, H) * SCALE - 2 * SCALE
    cx, cy = W * SCALE // 2, H * SCALE // 2
    box = (cx - diam // 2, cy - diam // 2, cx + diam // 2, cy + diam // 2)
    d.ellipse(box, outline=255, width=int(diam * 0.075))
    # achicar el texto hasta que quepa dentro del anillo
    while True:
        l, t, r, b = d.textbbox((0, 0), TEXT, font=font)
        if r - l <= diam * 0.72 and b - t <= diam * 0.56:
            break
        size = int(size * 0.95)
        font = ImageFont.truetype(FONT, size)
    x = (W * SCALE - (r - l)) // 2 - l
    y = (H * SCALE - (b - t)) // 2 - t
    d.text((x, y), TEXT, fill=255, font=font)
    small = big.resize((W, H), Image.LANCZOS)
    return [[small.getpixel((i, j)) > 110 for i in range(W)] for j in range(H)]


def braille(mask):
    def on(x, y):
        return 0 <= x < W and 0 <= y < H and mask[y][x]

    def lit(x, y):
        if not on(x, y):
            return False
        edge = any(not on(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        return edge or (x + y) % 2 == 0     # contorno solido, interior tramado

    lines = []
    for row in range(ROWS):
        line = ""
        for col in range(COLS):
            code = 0x2800
            for dy in range(4):
                for dx in range(2):
                    if lit(col * 2 + dx, row * 4 + dy):
                        code |= DOTS[dy][dx]
            line += chr(code)
        lines.append(line)
    return lines


if __name__ == "__main__":
    art = braille(render_mask())
    with open("ascii_art.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(art) + "\n")
    print("\n".join(art))
