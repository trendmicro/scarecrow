"""PPTX off-slide vector (structural).

A text box positioned off the visible slide canvas (10 inches off the top-left via
a negative EMU offset). PowerPoint clips rendering to the slide, so the box is never
drawn, but it lives in the shape tree and every shape-walking extractor reads its
text. Tagged via its `<p:cNvPr>` for clean().
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.pptx.vectors._common import add_offslide_textbox, tag_shape, remove_tagged_shapes


class OffSlideVector:
    name = "off_slide"
    format = "pptx"
    marker_kind = "structural"
    description = "off-canvas text box on the first slide (clipped in view, read by extractors)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        box = add_offslide_textbox(slide, payload)  # -9144000 EMU off top-left
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(OffSlideVector())
