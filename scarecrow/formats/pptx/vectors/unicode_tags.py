"""PPTX invisible-Unicode Tags-block vector (structural, research-only).

Encodes the payload into the Unicode Tags block (U+E0000-U+E007F) and puts it in a
run on the first slide. The codepoints render as nothing, so no formatting trick is
needed; the invisibility is in the characters themselves, and every extractor passes
them through. Carried over from the DOCX library; the same in-text-encoding idea,
format-independent (`_encodings.encode_tags`).

Excluded from `--all` (default_random=False): the DOCX per-vector experiment
found no current model decodes this encoding. Kept for research; select
with `--vectors unicode_tags`.
"""

from __future__ import annotations

from pptx.util import Emu

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.docx.vectors._encodings import encode_tags
from scarecrow.formats.pptx.vectors._common import (
    add_offslide_textbox, tag_shape, remove_tagged_shapes)


class UnicodeTagsVector:
    name = "unicode_tags"
    format = "pptx"
    marker_kind = "structural"
    description = "payload encoded in the invisible Unicode Tags block, in a slide run"
    default_random = False

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        box = add_offslide_textbox(slide, encode_tags(payload))
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(UnicodeTagsVector())
