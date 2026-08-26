"""Invisible-Unicode encodings for the in-text vectors.

These turn an ASCII payload into a run of codepoints that render as nothing but
are passed through by every text extractor. Unlike the structural vectors (which
hide a separate element), these carry the instruction *inside the text stream*
itself — our feasibility research flags this as the most arms-race-durable channel
(survives rendering; dies only to a targeted regex, not NFKC).

Two encodings, because model families differ (research: Anthropic models decode
Tags-block more readily, OpenAI/GPT-5.x decode zero-width binary more readily):

  tags  — Unicode Tags block: U+E0000 + ASCII codepoint, one invisible char per
          char. Round-trips exactly.
  zerow — zero-width binary: each byte -> 8 bits -> U+200B (0) / U+200C (1).
"""

from __future__ import annotations

_ZW0 = "​"  # zero-width space  = bit 0
_ZW1 = "‌"  # zero-width non-joiner = bit 1


def encode_tags(text: str) -> str:
    """ASCII -> Unicode Tags block (printable ASCII only; others pass through)."""
    return "".join(
        chr(0xE0000 + ord(c)) if 0x20 <= ord(c) <= 0x7E else c
        for c in text
    )


def encode_zero_width(text: str) -> str:
    """UTF-8 bytes -> zero-width binary (U+200B=0, U+200C=1)."""
    bits = "".join(format(b, "08b") for b in text.encode("utf-8"))
    return "".join(_ZW0 if b == "0" else _ZW1 for b in bits)
