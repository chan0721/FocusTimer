"""
Generate a minimalist FocusTimer icon as a multi-resolution .ico file.
No external dependencies beyond Python stdlib + numpy (already in requirements).
"""

import struct
import numpy as np
import os


def make_icon(output_path: str) -> None:
    """
    Creates a minimalist circular icon with a subtle inner ring
    representing focus/concentration.  Sizes: 16, 32, 48, 256 px.
    """

    def draw_circle(data: np.ndarray, cx: float, cy: float, r: float,
                    color: tuple) -> None:
        h, w = data.shape[:2]
        y, x = np.ogrid[:h, :w]
        mask = (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2
        data[mask] = color

    sizes = [16, 32, 48, 256]

    # Background: deep calm blue  #2c3e50
    bg = np.array([44, 62, 80, 255], dtype=np.uint8)
    # Accent ring: bright blue    #1a73e8
    accent = np.array([26, 115, 232, 255], dtype=np.uint8)
    # Inner dot / play hint: white
    white = np.array([255, 255, 255, 255], dtype=np.uint8)

    icon_entries = []  # (width, height, bmp_data)

    for size in sizes:
        # RGBA canvas
        img = np.tile(bg, (size, size, 1)).copy()

        cx = size / 2.0
        cy = size / 2.0

        # Outer filled circle (slightly darker background circle)
        draw_circle(img, cx, cy, size * 0.44, accent)

        # Inner hole (bg color) creates a ring effect
        draw_circle(img, cx, cy, size * 0.30, bg)

        # Center dot / focus point
        dot_r = size * 0.06
        if dot_r < 1:
            dot_r = 1
        draw_circle(img, cx, cy, dot_r, white)

        # Convert RGBA to BGRA (BMP format) and flip vertically
        bgra = img[:, :, [2, 1, 0, 3]]  # RGBA → BGRA
        bgra = np.ascontiguousarray(bgra[::-1])  # flip vertically

        # Build BMP data (DIB, 32-bit)
        h, w = size, size
        row_size = w * 4
        pixel_data = bgra.tobytes()

        # BITMAPINFOHEADER
        bih = struct.pack(
            "<IiiHHIIiiII",
            40,          # biSize
            w, h * 2,    # width, height×2 (top-down DIB uses double height)
            1,           # planes
            32,          # bpp
            0,           # compression (BI_RGB)
            len(pixel_data),
            0, 0, 0, 0,
        )

        bmp = bih + pixel_data
        icon_entries.append((size, size, bmp))

    # ── Write .ico file ───────────────────────────────────────────────
    with open(output_path, "wb") as f:
        # ICO header
        f.write(struct.pack("<HHH", 0, 1, len(icon_entries)))

        # Image directory entries
        offset = 6 + 16 * len(icon_entries)
        for w, h, data in icon_entries:
            actual_w = w if w < 256 else 0
            actual_h = h if h < 256 else 0
            f.write(struct.pack(
                "<BBBBHHII",
                actual_w, actual_h, 0, 0,  # width, height, palette, reserved
                1, 32,                     # color planes, bpp
                len(data), offset,
            ))
            offset += len(data)

        # Image data
        for _, _, data in icon_entries:
            f.write(data)


if __name__ == "__main__":
    dest = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "assets", "icon.ico")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    make_icon(dest)
    print(f"Icon written to {dest}")
