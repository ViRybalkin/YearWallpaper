from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFilter

# iPhone 16 Pro portrait pixels: 1206 x 2622  (Apple specs)
W, H = 1206, 2622

# Настройки
TZ = "Asia/Bangkok"            # чтобы "день" считался как тебе нужно
DOTS = 365
MARGIN = 120                   # отступ от краёв
DOT_RADIUS = 7                 # радиус точки
DOT_GAP = 14                   # расстояние между центрами точек
FILLED = (255, 255, 255, 235)  # цвет закрашенных точек (почти белый)
EMPTY  = (255, 255, 255, 70)   # цвет пустых точек (полупрозрачный)
BG1 = (20, 24, 35)             # фон-градиент (верх)
BG2 = (10, 12, 18)             # фон-градиент (низ)

OUT_PATH = "docs/wallpaper.png"


def day_of_year_local(tz: str) -> int:
    now = datetime.now(ZoneInfo(tz))
    return int(now.strftime("%j"))  # 001..366


def make_gradient_bg(w: int, h: int, c1, c2) -> Image.Image:
    img = Image.new("RGB", (w, h), c1)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    # лёгкое размытие чтобы выглядело мягче
    return img.filter(ImageFilter.GaussianBlur(radius=0.8))


def layout_grid(dots: int, w: int, h: int, margin: int, gap: int) -> tuple[int, int]:
    """
    Подбираем кол-во колонок/строк под доступную область.
    """
    avail_w = w - 2 * margin
    avail_h = h - 2 * margin

    # пробуем разумные варианты: больше строк, чем колонок (портрет)
    best = None
    for cols in range(10, 40):
        rows = math.ceil(dots / cols)
        needed_w = (cols - 1) * gap
        needed_h = (rows - 1) * gap
        if needed_w <= avail_w and needed_h <= avail_h:
            # чем больше используем площадь — тем лучше
            score = needed_w * needed_h
            if best is None or score > best[0]:
                best = (score, cols, rows)

    if best is None:
        # fallback
        cols = 19
        rows = math.ceil(dots / cols)
        return cols, rows

    return best[1], best[2]


def main() -> None:
    filled_count = day_of_year_local(TZ)
    # в високосный год будет 366 — можно либо закрашивать 365 и игнорировать 366,
    # либо “последнюю точку” держать как годовой бонус.
    filled_count = min(filled_count, DOTS)

    bg = make_gradient_bg(W, H, BG1, BG2).convert("RGBA")
    draw = ImageDraw.Draw(bg)

    cols, rows = layout_grid(DOTS, W, H, MARGIN, DOT_GAP)

    # центруем сетку
    total_w = (cols - 1) * DOT_GAP
    total_h = (rows - 1) * DOT_GAP
    start_x = (W - total_w) // 2
    start_y = (H - total_h) // 2

    # рисуем точки слева-направо, сверху-вниз
    i = 0
    for r in range(rows):
        for c in range(cols):
            if i >= DOTS:
                break
            x = start_x + c * DOT_GAP
            y = start_y + r * DOT_GAP

            color = FILLED if i < filled_count else EMPTY
            draw.ellipse(
                (x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS),
                fill=color,
            )
            i += 1

    bg.save(OUT_PATH, "PNG")
    print(f"Generated {OUT_PATH} with filled dots: {filled_count}/{DOTS} (TZ={TZ})")


if __name__ == "__main__":
    main()