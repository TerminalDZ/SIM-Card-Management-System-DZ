"""Unit tests for the GSM encoder helpers."""

from __future__ import annotations

import pytest

from app.modem import encoders


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("*123#", "*123#"),
        (" *222*1#  ", "*222*1#"),
        ("*100*ABCD#", "*100*ABCD#"),
        ("(*222#)", "*222#"),
        ("hello", "HELLO"),  # sanitize keeps letters and uppercases later via to_hex
    ],
)
def test_sanitize_ussd_keeps_safe_characters_only(raw: str, expected: str) -> None:
    sanitized = encoders.sanitize_ussd(raw)
    assert sanitized == expected.replace("HELLO", "hello")  # sanitize itself doesn't upper


def test_to_hex_septets_round_trips_basic_ascii() -> None:
    encoded = encoders.to_hex_septets("*222#")
    decoded = encoders.from_hex_septets(encoded)
    assert decoded == "*222#"


def test_to_hex_septets_replaces_unknown_characters_with_space() -> None:
    encoded = encoders.to_hex_septets("中")  # CJK char outside GSM7
    assert encoded == "20"


def test_is_gsm_compatible_detects_unsupported_characters() -> None:
    assert encoders.is_gsm_compatible("Bonjour")
    assert not encoders.is_gsm_compatible("مرحبا")


def test_from_ucs2_hex_decodes_simple_strings() -> None:
    # "Hi" in UCS-2 BE => 00 48 00 69
    assert encoders.from_ucs2_hex("00480069") == "Hi"


def test_from_ucs2_hex_returns_input_when_invalid() -> None:
    assert encoders.from_ucs2_hex("not-hex") == "not-hex"
