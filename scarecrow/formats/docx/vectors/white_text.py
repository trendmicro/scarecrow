"""DOCX background-coloured 1pt-text vector.

Like the flagship `vanish` vector but without the `w:vanish` property — the run is
hidden purely by matching the page background and being one point tall. Useful as a
distinct, separately measurable technique: some pipelines strip `w:vanish` runs
specifically, and this one survives that (though it dies to a colour/size check).
Structural: the run is taggable, so clean() finds it by marker.

Dark-mode robustness: instead of a hardcoded white RGB (which only disappears on a
white page, and shows up on a dark-mode canvas or a coloured background), the run
colour references the document's theme background via `w:themeColor="background1"`.
A viewer that honours the theme renders the glyphs in whatever the background colour
actually is, in light *or* dark mode. We keep an RGB fallback so viewers that ignore
the theme reference still get a sensible colour. This does not defeat a strip-pass
that looks for background-matched colour; for strip-resistance the off-position
vectors (`off_page`) are the durable class.
"""

from __future__ import annotations

from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.docx.vectors._common import preserve_space, remove_tagged_elements


class WhiteTextVector:
    name = "white_text"
    format = "docx"
    marker_kind = "structural"
    description = "background-coloured 1pt text run (invisible to the eye, read by extractors)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        run = para.add_run(payload)
        # RGB fallback (white) for viewers that ignore the theme reference...
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        # ...plus a theme-background reference so the glyphs track the actual page
        # colour in light OR dark mode. python-docx does not expose themeColor, so
        # set it on the color element directly.
        color_el = run._r.find(qn("w:rPr")).find(qn("w:color"))
        color_el.set(qn("w:themeColor"), "background1")
        run.font.size = Pt(1)
        preserve_space(run)
        marker.tag_element(run._r, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        remove_tagged_elements(doc.element.body, marker, self.name)  # type: ignore[attr-defined]


register(WhiteTextVector())
