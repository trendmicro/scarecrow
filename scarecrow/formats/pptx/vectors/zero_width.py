"""PPTX zero-width-binary vector (structural, research-only).

Encodes the payload as zero-width binary (U+200B=0, U+200C=1) in a run on the first
slide. Reuses the DOCX encoder (`_encodings.encode_zero_width`); format-independent.

Excluded from `--all` (default_random=False): the DOCX per-vector experiment
found no current model decodes this encoding. Kept for research; select
with `--vectors zero_width`.
"""

from __future__ import annotations

from pptx.util import Emu

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.docx.vectors._encodings import encode_zero_width
from scarecrow.formats.pptx.vectors._common import (
    add_offslide_textbox, tag_shape, remove_tagged_shapes)


class ZeroWidthVector:
    name = "zero_width"
    format = "pptx"
    marker_kind = "structural"
    description = "payload encoded in zero-width binary (U+200B/U+200C), in a slide run"
    default_random = False

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        box = add_offslide_textbox(slide, encode_zero_width(payload))
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(ZeroWidthVector())
