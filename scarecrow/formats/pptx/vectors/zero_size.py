"""PPTX zero-size vector (structural).

A text box with zero width and height. There is no bounding box in which to draw
glyphs, so it renders as nothing, but the `<p:txBody>` text is fully extracted.
A distinct hiding mechanism from off_slide (which relies on canvas clipping) — some
sanitizers key on off-canvas position but not on zero dimensions. Tagged for clean().
"""

from __future__ import annotations

from pptx.util import Emu

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.pptx.vectors._common import tag_shape, remove_tagged_shapes


class ZeroSizeVector:
    name = "zero_size"
    format = "pptx"
    marker_kind = "structural"
    description = "zero-size text box on the first slide (no bounding box to render)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        box = slide.shapes.add_textbox(Emu(0), Emu(0), Emu(914400), Emu(457200))
        box.text_frame.text = payload
        box.width = Emu(0)
        box.height = Emu(0)
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(ZeroSizeVector())
