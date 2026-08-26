"""PPTX background-coloured-text vector (structural).

A normal on-slide text box whose font colour matches the slide background. The glyphs
have zero contrast so a human sees nothing, but every extractor reads the `<a:t>` run
text without consulting colour. The box is tagged via its `<p:cNvPr>` so clean()
removes it.

Dark-mode robustness: instead of a hardcoded white RGB (which only disappears on a
white slide, and shows up against a dark theme or a coloured slide), the run colour
references the theme background via `<a:schemeClr val="bg1"/>`. A renderer that
honours the theme paints the glyphs in whatever the slide's background colour actually
is, in a light OR dark theme. This does not defeat a strip-pass that looks for
background-matched colour; for strip-resistance the off-position vectors (`off_slide`)
are the durable class.
"""

from __future__ import annotations

from lxml import etree
from pptx.util import Emu, Pt

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.pptx.vectors._common import qn_a, tag_shape, remove_tagged_shapes


class WhiteTextVector:
    name = "white_text"
    format = "pptx"
    marker_kind = "structural"
    description = "background-coloured text box on the first slide (invisible to the eye, read by extractors)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        box = slide.shapes.add_textbox(Emu(0), Emu(0), Emu(914400), Emu(457200))
        run = box.text_frame.paragraphs[0].add_run()
        run.text = payload
        run.font.size = Pt(1)                            # also tiny, belt-and-suspenders
        # Theme-background fill so the glyphs track the actual slide background colour
        # in a light OR dark theme: <a:solidFill><a:schemeClr val="bg1"/></a:solidFill>
        # on the run's <a:rPr>. python-pptx only exposes srgbClr, so build it directly.
        rpr = run._r.get_or_add_rPr()
        for existing in rpr.findall(qn_a("solidFill")):
            rpr.remove(existing)
        fill = etree.SubElement(rpr, qn_a("solidFill"))
        etree.SubElement(fill, qn_a("schemeClr")).set("val", "bg1")
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        for slide in doc.slides:                  # type: ignore[attr-defined]
            remove_tagged_shapes(slide, marker, self.name)


register(WhiteTextVector())
