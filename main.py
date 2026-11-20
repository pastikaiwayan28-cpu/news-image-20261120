#!/usr/bin/env python3
"""news-image-20261120 entry (Python 3.13, standard library only).

Copies the entry.png beside this file to /output/entry.png, byte for
byte, after validating it: PNG signature, IHDR dimensions 1024x1024,
total size at most 1 MiB, and a complete IEND chunk (no truncation).
Verifies the copy by comparing SHA-256 hashes.

Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for
/output, as in the kit starter:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import struct
import sys

MAX_BYTES = 1 * 1024 * 1024
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def fail(message):
    print(f"main.py: error: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_png(data):
    if len(data) > MAX_BYTES:
        fail(f"entry.png is {len(data)} bytes, over the 1 MiB limit")
    if len(data) < 8 or data[:8] != PNG_SIGNATURE:
        fail("entry.png is not a PNG (bad signature)")
    if len(data) < 8 + 25:
        fail("entry.png is truncated (no IHDR)")
    length, ctype = struct.unpack(">I4s", data[8:16])
    if ctype != b"IHDR" or length != 13:
        fail("entry.png has no valid IHDR chunk first")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (1024, 1024):
        fail(f"entry.png is {width}x{height}, must be 1024x1024")
    # Walk the chunk list to confirm a well-formed file ending in IEND.
    pos = 8
    seen_iend = False
    while pos + 8 <= len(data):
        length, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 8 + length + 4  # chunk header + data + CRC
        if end > len(data):
            fail(f"entry.png is truncated inside {ctype!r} chunk")
        if ctype == b"IEND":
            if length != 0 or end != len(data):
                fail("entry.png has trailing data after IEND")
            seen_iend = True
            break
        pos = end
    if not seen_iend:
        fail("entry.png has no IEND chunk (truncated)")
    return width, height


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    dst = os.path.join(out_dir, "entry.png")

    try:
        with open(src, "rb") as fh:
            data = fh.read()
    except FileNotFoundError:
        fail(f"entry.png not found beside main.py ({src})")

    width, height = validate_png(data)
    source_hash = hashlib.sha256(data).hexdigest()

    os.makedirs(out_dir, exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(data)

    with open(dst, "rb") as fh:
        copied = fh.read()
    copied_hash = hashlib.sha256(copied).hexdigest()
    if copied_hash != source_hash:
        fail("copy verification failed: sha256 mismatch after copy")

    print(f"entry.png: {len(data)} bytes, {width}x{height}, "
          f"sha256={source_hash}")
    print(f"copied to {dst} (sha256 verified identical)")


if __name__ == "__main__":
    main()
