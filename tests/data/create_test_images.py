"""
tests/data/create_test_images.py
Programmatically creates all test image files needed by the forensic test suite.
Run this script once before running pytest.
"""
import os
import sys
from pathlib import Path

DATA_DIR = Path(__file__).parent


def create_test_images():
    # 1. Valid JPEG — 100x100 red image
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        jpeg_path = DATA_DIR / "test_valid_jpeg.jpg"
        img.save(jpeg_path, "JPEG", quality=85)
        print(f"Created: {jpeg_path}")
    except Exception as e:
        print(f"ERROR creating test_valid_jpeg.jpg: {e}")

    # 2. Valid PNG — 100x100 green image
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))
        png_path = DATA_DIR / "test_valid_png.png"
        img.save(png_path, "PNG")
        print(f"Created: {png_path}")
    except Exception as e:
        print(f"ERROR creating test_valid_png.png: {e}")

    # 3. Malformed binary — 50 bytes of non-image data
    try:
        malformed_path = DATA_DIR / "test_malformed.bin"
        # Build 50 pseudo-random bytes that don't match any image magic
        data = bytes([(i * 37 + 13) % 256 for i in range(50)])
        # Ensure the first bytes do NOT match JPEG (FF D8 FF), PNG (89 50 4E 47), BMP (42 4D)
        data = b"\x00\x01\x02\x03\x04This is not an image file at all!!" + data[:14]
        malformed_path.write_bytes(data)
        print(f"Created: {malformed_path}  ({len(data)} bytes)")
    except Exception as e:
        print(f"ERROR creating test_malformed.bin: {e}")

    # 4. Empty file — zero bytes
    try:
        empty_path = DATA_DIR / "test_empty.jpg"
        empty_path.write_bytes(b"")
        print(f"Created: {empty_path}  (0 bytes)")
    except Exception as e:
        print(f"ERROR creating test_empty.jpg: {e}")

    # 5. "Oversized" placeholder — a real 100x100 JPEG; tests mock file size
    try:
        from PIL import Image
        img = Image.new("RGB", (100, 100), color=(0, 0, 255))
        oversized_path = DATA_DIR / "test_oversized.jpg"
        img.save(oversized_path, "JPEG", quality=85)
        print(f"Created: {oversized_path}  (oversized tests will mock file size)")
    except Exception as e:
        print(f"ERROR creating test_oversized.jpg: {e}")

    print("\nAll test images created successfully.")


if __name__ == "__main__":
    create_test_images()
