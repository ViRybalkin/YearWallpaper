from __future__ import annotations

import math
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFilter


# Итоговый размер под iPhone 16 Pro (portrait)
W, H = 1206, 2622

# Сглаживание (рисуем больше и уменьшаем)
SCALE = 4

# Даты
TZ = "Asia/Bangkok"
DOTS = 365

# Сетка
ROWS = 25
COLS = math.ceil(DOTS / ROWS)  # 15

# Точки (как на референсе: крупнее, плотнее)
DOT_RADIUS = 10          # было 7 -> стало 10 (крупнее)
DOT_EDGE_GAP = 4         # расстояние МЕЖДУ КРАЯМИ точек (чуть больше, чтобы выглядело “пузырями”)
DOT_GAP = DOT_RADIUS * 2 + DOT_EDGE_GAP

# Цвета
PAST = (255, 255, 255, 255)      # белый
TODAY = (220, 40, 40, 255)       # красный
FUTURE = (180, 180, 180, 170)    # серый (чуть прозрачный, как на референсе)

# Фон (однотонный, как на примере)
BG_SOLID = (108, 181, 128)        # зелёный фон (можешь менять)

OUT_PATH = "docs/wallpaper.png"


def day_of_year_local(tz: str) -> int:
    now = datetime.now(ZoneInfo(tz))
    return int(now.strftime("%j"))  # 1..366


def make_solid_bg(w: int, h: int, rgb) -> Image.Image:
    # лёгкое размытие “на всякий”, чтобы не было banding на градиентах экрана
    img = Image.new("RGB", (w, h), rgb)
    return img.filter(ImageFilter.GaussianBlur(radius=0.4)).convert("RGBA")


def main() -> None:
    doy = day_of_year_local(TZ)

    # прошедшие дни: 1..(doy-1)
    past_count = min(max(doy - 1, 0), DOTS)
    today_index = doy if 1 <= doy <= DOTS else None  # в високосный 366 — today не рисуем

    # scaled canvas
    w2, h2 = W * SCALE, H * SCALE
    dot_r2 = DOT_RADIUS * SCALE
    dot_gap2 = DOT_GAP * SCALE

    bg2 = make_solid_bg(w2, h2, BG_SOLID)
    draw = ImageDraw.Draw(bg2)

    # Размер сетки
    total_w2 = (COLS - 1) * dot_gap2
    total_h2 = (ROWS - 1) * dot_gap2
    start_x2 = (w2 - total_w2) // 2

    # Позиционирование “как на iOS lock screen” (опущено ниже)
    # Под референс: больше отступ сверху + дополнительный сдвиг вниз
    TOP_SAFE_OFFSET2 = int(H * 0.24) * SCALE     # было 0.18 -> 0.24 (ниже от часов)
    EXTRA_Y_OFFSET2 = int(H * 0.10) * SCALE      # дополнительный сдвиг вниз

    start_y2 = (
        TOP_SAFE_OFFSET2
        + (h2 - TOP_SAFE_OFFSET2 - total_h2) // 2
        + EXTRA_Y_OFFSET2
    )

    # Рисуем точки
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

    # downscale for smooth dots
    final_img = bg2.resize((W, H), resample=Image.LANCZOS)
    final_img.save(OUT_PATH, "PNG")

    print(
        f"Generated {OUT_PATH} | DOY={doy} | past={past_count} | today={today_index} "
        f"| grid={ROWS}x{COLS} | dot_radius={DOT_RADIUS}px | edge_gap={DOT_EDGE_GAP}px"
    )


if __name__ == "__main__":
    main()