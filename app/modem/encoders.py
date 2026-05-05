"""GSM 7-bit and hex encoding helpers used for USSD over AT.

Pure functions — no I/O, no state — so they are trivial to unit-test.
"""

from __future__ import annotations

import re

# Default GSM 7-bit alphabet (3GPP TS 23.038 §6.2.1).
_GSM_ALPHABET: str = (
    "@£$¥èéùìòÇ\nØø\rÅå"
    "Δ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ"
    " !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§"
    "¿abcdefghijklmnopqrstuvwxyzäöñüà"
)

_GSM_INDEX: dict[str, int] = {ch: idx for idx, ch in enumerate(_GSM_ALPHABET)}

_USSD_SAFE = re.compile(r"[^0-9*#+A-Za-z]")


def is_gsm_compatible(text: str) -> bool:
    """Return ``True`` if every character in *text* is in the GSM 7-bit alphabet."""
    return all(ch in _GSM_INDEX for ch in text)


def sanitize_ussd(command: str) -> str:
    """Strip characters that would never appear in a legal USSD command."""
    return _USSD_SAFE.sub("", command).strip()


def to_hex_septets(text: str) -> str:
    """Encode *text* as the hexadecimal representation of its GSM-7 codepoints.

    This is the format Huawei modems accept on ``AT+CUSD=1,"<hex>",15`` when
    the command contains no DCS-incompatible characters.
    """
    parts: list[str] = []
    for ch in text:
        idx = _GSM_INDEX.get(ch)
        if idx is None:
            # Fall back to space (0x20) for characters outside the alphabet
            idx = _GSM_INDEX[" "]
        parts.append(f"{idx:02X}")
    return "".join(parts)


def from_hex_septets(hex_text: str) -> str:
    """Inverse of :func:`to_hex_septets`."""
    if not hex_text:
        return ""
    if len(hex_text) % 2:
        hex_text = hex_text[:-1]
    out: list[str] = []
    for i in range(0, len(hex_text), 2):
        try:
            code = int(hex_text[i : i + 2], 16)
        except ValueError:
            continue
        if 0 <= code < len(_GSM_ALPHABET):
            out.append(_GSM_ALPHABET[code])
        else:
            out.append(chr(code))
    return "".join(out)


def from_ucs2_hex(hex_text: str) -> str:
    """Decode a UCS-2 (UTF-16BE) hex string returned by ``+CUSD``."""
    if not hex_text or len(hex_text) % 4:
        return hex_text
    try:
        return bytes.fromhex(hex_text).decode("utf-16-be", errors="replace")
    except ValueError:
        return hex_text
