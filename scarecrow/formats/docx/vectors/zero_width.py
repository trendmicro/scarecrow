"""DOCX invisible-Unicode zero-width-binary vector.

Encodes the payload as zero-width binary (each byte -> 8 bits -> U+200B / U+200C)
and adds it as a body run. Renders as nothing; every extractor passes the
codepoints through. The zero-width encoding is the one OpenAI/GPT-5.x-family
models tend to decode (vs Tags-block for Anthropic), so shipping both encodings
covers both families — hence a separate vector from `unicode_tags`.

Same in-text-encoding family as `unicode_tags`. Structural: the run is taggable.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.docx.vectors._common import preserve_space, remove_tagged_elements
from scarecrow.formats.docx.vectors._encodings import encode_zero_width


class ZeroWidthVector:
    name = "zero_width"
    format = "docx"
    marker_kind = "structural"
    description = "payload encoded in zero-width binary (U+200B/U+200C), in the text stream"
    # Excluded from `--all`: the per-vector experiment found no model
    # decoded this encoding (0/14, no canary echoes). Kept in the library for
    # research; select explicitly with `--vectors zero_width`.
    default_random = False

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        run = para.add_run(encode_zero_width(payload))
        preserve_space(run)
        marker.tag_element(run._r, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        remove_tagged_elements(doc.element.body, marker, self.name)  # type: ignore[attr-defined]


register(ZeroWidthVector())
