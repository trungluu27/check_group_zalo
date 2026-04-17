"""
Script to create a simple placeholder icon for the app.
Run this script to generate resources/icon.ico (Windows) and resources/icon.icns (macOS placeholder).

Requirements: pip install Pillow
"""

from pathlib import Path
import struct
import zlib


def create_simple_ico(path: Path, size: int = 64):
    """
    Create a minimal valid .ico file with a solid blue square.
    Uses pure Python (no Pillow required) by writing raw BMP data.
    """
    # --- BMP pixel data (BGRA, bottom-up) ---
    # Blue = #0068FF, solid square
    b, g, r, a = 0xFF, 0x68, 0x00, 0xFF  # BGRA order
    row = bytes([b, g, r, a] * size)
    pixel_data = row * size  # All rows identical

    # BITMAPINFOHEADER (40 bytes) for ICO (height doubled per spec)
    bih = struct.pack(
        '<IiiHHIIiiII',
        40,           # biSize
        size,         # biWidth
        size * 2,     # biHeight (doubled in ICO format)
        1,            # biPlanes
        32,           # biBitCount
        0,            # biCompression (BI_RGB)
        0,            # biSizeImage
        0, 0,         # biXPelsPerMeter, biYPelsPerMeter
        0, 0          # biClrUsed, biClrImportant
    )

    # AND mask (1-bit, all 0 = fully opaque) — (size * ceil(size/8)) bytes, padded to 4-byte rows
    mask_row_bytes = ((size + 31) // 32) * 4
    and_mask = bytes(mask_row_bytes * size)

    image_data = bih + pixel_data + and_mask
    image_size = len(image_data)

    # ICO header (6 bytes) + ICONDIRENTRY (16 bytes)
    ico_header = struct.pack('<HHH', 0, 1, 1)  # Reserved, Type=1(ICO), Count=1
    entry_offset = 6 + 16  # Header + one entry
    icon_entry = struct.pack(
        '<BBBBHHII',
        size if size < 256 else 0,  # Width (0 = 256)
        size if size < 256 else 0,  # Height (0 = 256)
        0,            # ColorCount
        0,            # Reserved
        1,            # Planes
        32,           # BitCount
        image_size,   # BytesInRes
        entry_offset  # ImageOffset
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(ico_header + icon_entry + image_data)
    print(f"[OK] Created: {path} ({path.stat().st_size} bytes)")


def create_simple_png_bytes(size: int = 64) -> bytes:
    """Create a minimal valid PNG bytes (blue square) — pure Python."""
    # PNG signature
    sig = b'\x89PNG\r\n\x1a\n'

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        length = struct.pack('>I', len(data))
        crc = struct.pack('>I', zlib.crc32(chunk_type + data) & 0xFFFFFFFF)
        return length + chunk_type + data + crc

    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0)
    ihdr = make_chunk(b'IHDR', ihdr_data)

    # IDAT — RGBA rows (filter byte 0 per row)
    r, g, b = 0x00, 0x68, 0xFF  # Blue
    row = bytes([0] + [r, g, b] * size)  # Filter=0 + RGB pixels
    raw_rows = row * size
    idat = make_chunk(b'IDAT', zlib.compress(raw_rows))

    # IEND
    iend = make_chunk(b'IEND', b'')

    return sig + ihdr + idat + iend


def create_icns_placeholder(path: Path, size: int = 64):
    """
    Create a minimal valid .icns file with a PNG icon.
    Real macOS app icons should use proper icns with multiple sizes,
    but this is sufficient for development/testing.
    """
    png_data = create_simple_png_bytes(size)

    # ICNS uses 4-byte OSType tags
    # 'ic07' = 128x128, 'ic08' = 256x256, 'ic04' = 16x16
    # Use 'icp4' for 16x16 PNG (safe minimum)
    icon_type = b'icp4'  # 16x16 PNG
    icon_data = icon_type + struct.pack('>I', 8 + len(png_data)) + png_data

    # ICNS header: 'icns' + total size (big-endian uint32)
    total_size = 8 + len(icon_data)
    icns_bytes = b'icns' + struct.pack('>I', total_size) + icon_data

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(icns_bytes)
    print(f"[OK] Created: {path} ({path.stat().st_size} bytes)")


if __name__ == '__main__':
    resources = Path('resources')

    # Windows icon
    create_simple_ico(resources / 'icon.ico', size=64)

    # macOS icon (placeholder — replace with proper .icns for production)
    create_icns_placeholder(resources / 'icon.icns', size=16)

    print()
    print("Icons created successfully.")
    print("For production, replace with proper icons:")
    print("  Windows: resources/icon.ico  (multi-size ICO, e.g. 16/32/48/64/128/256px)")
    print("  macOS:   resources/icon.icns (use iconutil on macOS to create proper icns)")
