"""PPTX tiny-font vector (structural).

An on-slide text run shrunk to 0.01pt (`sz="1"`, in hundredths of a point). At any
practical screen DPI the font rasteriser produces zero pixels, so it is invisible,
but the `<a:t>` text is read by every extractor. python-pptx enforces a minimum of
1pt (`Pt(0.5)` raises ValueError), so we set the run to Pt(1) and then override the
`sz` attribute below the minimum directly via lxml.
"""

from __future__ import annotations

from pptx.util import Emu, Pt

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.pptx.vectors._common import qn_a, tag_shape, remove_tagged_shapes


class TinyFontVector:
    name = "tiny_font"
    format = "pptx"
    marker_kind = "structural"
    description = "0.01pt text run on the first slide (sub-pixel, read by extractors)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        box = slide.shapes.add_textbox(Emu(0), Emu(0), Emu(914400), Emu(457200))
        run = box.text_frame.paragraphs[0].add_run()
        run.text = payload
        run.font.size = Pt(1)                     # highest-level API floor
        # Drop below the enforced minimum: sz is in hundredths of a point, so
        # "1" = 0.01pt. python-pptx won't set this, but the XML accepts it.
        rPr = run._r.find(qn_a("rPr"))
        if rPr is not None:
            rPr.set("sz", "1")
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(TinyFontVector())
