"""PPTX alt-text vector (structural).

The payload goes in the accessibility description (`descr` attribute on a shape's
`<p:cNvPr>`). Alt-text is never rendered on the slide; screen readers vocalise it
and several extractors (python-pptx via the element, Tika) surface it. We attach it
to a tiny off-slide text box so nothing visible is added, then tag that shape.

Structural: the whole tagged shape is removed by clean(). We deliberately put the
payload only in `descr` (not the shape's text) so this exercises the alt-text
channel specifically.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.pptx.vectors._common import (
    add_offslide_textbox, cNvPr_of, tag_shape, remove_tagged_shapes)


class AltTextVector:
    name = "alt_text"
    format = "pptx"
    marker_kind = "structural"
    description = "payload in a shape's alt-text (descr on p:cNvPr)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        # An off-slide carrier so nothing visible is added; the payload lives in
        # descr, not the box's own (empty) text.
        box = add_offslide_textbox(slide, "")
        cnv = cNvPr_of(box)
        if cnv is not None:
            cnv.set("descr", payload)
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(AltTextVector())
