"""Text cleaner — encoding detection, whitespace normalization, control char removal."""

from __future__ import annotations

import re

# Encodings to try in order
ENCODINGS = ("utf-8-sig", "utf-8", "gbk", "gb18030", "gb2312", "big5", "shift_jis", "euc-kr", "latin-1")


def detect_and_decode(raw: bytes) -> tuple[str, str]:
    """Detect encoding and decode bytes. Returns (text, encoding_name).

    Raises ValueError if no encoding produces valid text.
    """
    for enc in ENCODINGS:
        try:
            text = raw.decode(enc)
            # Verify it looks like real text (not random bytes decoded as latin-1)
            if enc == "latin-1" and _has_too_many_control_chars(text):
                continue
            return text, enc
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError("无法识别文件编码，请将文件转换为 UTF-8 后重试")


def _has_too_many_control_chars(text: str) -> bool:
    """Check if decoded text has suspiciously many control characters."""
    control_count = sum(1 for c in text[:1000] if ord(c) < 32 and c not in "\n\r\t")
    return control_count > len(text[:1000]) * 0.05


def clean_text(text: str) -> str:
    """Normalize and clean text content.

    - Normalize line endings to \n
    - Remove BOM
    - Remove control characters (except \n, \r, \t)
    - Normalize unicode to NFC
    - Collapse runs of blank lines (max 2)
    - Strip trailing whitespace per line
    """
    import unicodedata

    # Remove BOM
    text = text.lstrip("﻿")

    # Normalize unicode
    text = unicodedata.normalize("NFC", text)

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove control characters (keep \n \t)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Strip trailing whitespace per line
    lines = [line.rstrip() for line in text.split("\n")]

    # Collapse runs of 3+ blank lines into 2
    result = []
    blank_count = 0
    for line in lines:
        if line.strip() == "":
            blank_count += 1
            if blank_count <= 2:
                result.append("")
        else:
            blank_count = 0
            result.append(line)

    return "\n".join(result).strip()
