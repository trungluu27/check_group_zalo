"""
Build resources/icon.ico from resources/icon.png.

Windows picks a different size out of the .ico depending on where the icon is
shown — 16px in the taskbar and Explorer's detail view, 32px on the desktop,
256px in the Properties dialog. A single-size .ico makes Windows rescale on the
fly and look rough, so every size is written into the file.

Build-time only: Pillow is not a runtime dependency of the app and is excluded
from the PyInstaller bundle.

Usage:
    venv\\Scripts\\python.exe resources\\make_icon.py
"""

from pathlib import Path

from PIL import Image

RESOURCES = Path(__file__).parent
SOURCE = RESOURCES / "icon.png"
TARGET = RESOURCES / "icon.ico"

# Sizes Windows actually asks for.
SIZES = [16, 32, 48, 64, 128, 256]


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit(f"[ERROR] Source image not found: {SOURCE}")

    img = Image.open(SOURCE)
    print(f"[INFO] Source: {SOURCE.name}  {img.width}x{img.height}  {img.mode}")

    # RGBA keeps the transparent background; without it the icon gets a black box.
    if img.mode != "RGBA":
        print(f"[INFO] Converting {img.mode} -> RGBA")
        img = img.convert("RGBA")

    if img.width != img.height:
        side = max(img.width, img.height)
        square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
        square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
        img = square
        print(f"[INFO] Padded to square: {side}x{side}")

    # Pillow rescales to each requested size with LANCZOS internally.
    img.save(TARGET, format="ICO", sizes=[(s, s) for s in SIZES])

    print(f"[OK] Wrote {TARGET} ({TARGET.stat().st_size / 1024:.0f} KB)")
    print(f"     Sizes: {', '.join(f'{s}x{s}' for s in SIZES)}")


if __name__ == "__main__":
    main()
