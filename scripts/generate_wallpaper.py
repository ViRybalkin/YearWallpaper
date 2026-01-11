from __future__ import annotations

import math
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFilter, ImageOps

# iPhone 16 Pro (portrait) pixels
W, H = 1206, 2622

# Настройки
TZ = "Asia/Bangkok"
DOTS = 365

# Сетка: ровно 25 рядов
ROWS = 25
COLS = math.ceil(DOTS / ROWS)  # 365/25 -> 15 колонок (375 ячеек, 10 лишних не рисуем)

# Точки: gap между КРАЯМИ = 2px
DOT_RADIUS = 7                  # радиус точки (диаметр 14)
DOT_EDGE_GAP = 2                # gap между точками (между краями)
DOT_GAP = DOT_RADIUS * 2 + DOT_EDGE_GAP  # расстояние между центрами (16)

# Цвета:
PAST = (255, 255, 255, 255)      # прошедшие дни - белый
TODAY = (220, 40, 40, 255)       # текущий день - красный
FUTURE = (160, 160, 160, 140)    # будущие дни - серый (полупрозрачный)

# Фон: либо картинка (если положишь), либо градиент
BG_PATH = "assets/bg.jpg"         # можно заменить на .png/.webp или оставить как есть
BG1 = (20, 24, 35)                # градиент сверху
BG2 = (10, 12, 18)                # градиент снизу

OUT_PATH = "docs/wallpaper.png"


def day_of_year_local(tz: str) -> int:
    now = datetime.now(ZoneInfo(tz))
    return int(now.strftime("%j"))  # 1..366


def make_gradient_bg(w: int, h: int, c1, c2) -> Image.Image:
    img = Image.new("RGB", (w, h), c1)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img.filter(ImageFilter.GaussianBlur(radius=0.8)).convert("RGBA")


def make_bg_from_image(path: str, w: int, h: int) -> Image.Image:
    img = Image.open(path).convert("RGB")
    # cover без искажений
    img = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))

    # лёгкое затемнение, чтобы точки читались
    overlay = Image.new("RGB", (w, h), (0, 0, 0))
    img = Image.blend(img, overlay, 0.15)
    return img.convert("RGBA")


def main() -> None:
    doy = day_of_year_local(TZ)

    # 365 точек. В високосный день 366 просто делаем все прошедшими (без "сегодня").
    past_count = min(max(doy - 1, 0), DOTS)    # сколько точно "прошло"
    today_index = doy if 1 <= doy <= DOTS else None

    # Фон
    if BG_PATH and os.path.exists(BG_PATH):
        bg = make_bg_from_image(BG_PATH, W, H)
    else:
        bg = make_gradient_bg(W, H, BG1, BG2)

    draw = ImageDraw.Draw(bg)

    # центровка сетки
    total_w = (COLS - 1) * DOT_GAP
    total_h = (ROWS - 1) * DOT_GAP
    start_x = (W - total_w) // 2
    start_y = (H - total_h) // 2

    i = 0
    for r in range(ROWS):
        for c in range(COLS):
            if i >= DOTS:
                break

            x = start_x + c * DOT_GAP
            y = start_y + r * DOT_GAP

            day_index = i + 1  # 1..365

            if day_index <= past_count:
                color = PAST
            elif today_index is not None and day_index == today_index:
                color = TODAY
            else:
                color = FUTURE

            draw.ellipse(
                (x - DOT_RADIUS, y - DOT_RADIUS, x + DOT_RADIUS, y + DOT_RADIUS),
                fill=color,
            )
            i += 1

    bg.save(OUT_PATH, "PNG")
    print(
        f"Generated {OUT_PATH} | DOY={doy} | past={past_count} | today={today_index} | grid={ROWS}x{COLS} | gap(edge)={DOT_EDGE_GAP}px"
    )


if __name__ == "__main__":
    main()