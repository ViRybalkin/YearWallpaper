from __future__ import annotations

import math
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFilter, ImageOps

# Итоговый размер под iPhone 16 Pro (portrait)
W, H = 1206, 2622

# Рендерим в большем разрешении и потом уменьшаем -> сглаживание точек
SCALE = 4  # 3 или 4 (4 гладче)

# Настройки
TZ = "Asia/Bangkok"
DOTS = 365

# Сетка: ровно 25 рядов
ROWS = 25
COLS = math.ceil(DOTS / ROWS)  # 15 колонок

# Точки: gap между КРАЯМИ = 2px (в финальном размере)
DOT_RADIUS = 7
DOT_EDGE_GAP = 2
DOT_GAP = DOT_RADIUS * 2 + DOT_EDGE_GAP  # расстояние между центрами

# Цвета
PAST = (255, 255, 255, 255)      # прошедшие
TODAY = (220, 40, 40, 255)       # сегодня
FUTURE = (160, 160, 160, 140)    # будущее

# Фон
BG_PATH = "assets/bg.jpg"
BG1 = (108, 181, 128)
BG2 = (108, 181, 128)

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
    # cover: без искажений, лишнее обрезается
    img = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
    # лёгкое затемнение, чтобы точки читались
    overlay = Image.new("RGB", (w, h), (0, 0, 0))
    img = Image.blend(img, overlay, 0.15)
    return img.convert("RGBA")


def main() -> None:
    doy = day_of_year_local(TZ)

    past_count = min(max(doy - 1, 0), DOTS)
    today_index = doy if 1 <= doy <= DOTS else None

    # Масштабируем параметры под supersampling
    w2, h2 = W * SCALE, H * SCALE
    dot_r2 = DOT_RADIUS * SCALE
    dot_gap2 = DOT_GAP * SCALE

    # Смещения под Lock Screen iOS (в финальном размере) -> переводим в scaled
    top_safe_offset2 = int(H * 0.18) * SCALE
    extra_y_offset2 = int(H * 0.06) * SCALE

    # Фон в большом разрешении
    if BG_PATH and os.path.exists(BG_PATH):
        bg2 = make_bg_from_image(BG_PATH, w2, h2)
    else:
        bg2 = make_gradient_bg(w2, h2, BG1, BG2)

    draw = ImageDraw.Draw(bg2)

    # Центровка сетки в scaled координатах
    total_w2 = (COLS - 1) * dot_gap2
    total_h2 = (ROWS - 1) * dot_gap2
    start_x2 = (w2 - total_w2) // 2

    start_y2 = (
        top_safe_offset2
        + (h2 - top_safe_offset2 - total_h2) // 2
        + extra_y_offset2
    )

    # Рисуем точки (в большом разрешении)
    i = 0
    for r in range(ROWS):
        for c in range(COLS):
            if i >= DOTS:
                break

            x = start_x2 + c * dot_gap2
            y = start_y2 + r * dot_gap2

            day_index = i + 1
            if day_index <= past_count:
                color = PAST
            elif today_index is not None and day_index == today_index:
                color = TODAY
            else:
                color = FUTURE

            draw.ellipse(
                (x - dot_r2, y - dot_r2, x + dot_r2, y + dot_r2),
                fill=color,
            )
            i += 1

    # Downscale до финального размера -> сглаживание
    final_img = bg2.resize((W, H), resample=Image.LANCZOS)
    final_img.save(OUT_PATH, "PNG")

    print(
        f"Generated {OUT_PATH} | DOY={doy} | past={past_count} | today={today_index} "
        f"| grid={ROWS}x{COLS} | scale={SCALE}x"
    )


if __name__ == "__main__":
    main()