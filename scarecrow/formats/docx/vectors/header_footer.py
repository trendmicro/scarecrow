"""DOCX header/footer vector.

Places the payload as a white 1pt run in the first section's header. Header/footer
text lives in a separate XML part (`word/header1.xml`), which some extractors pull
in (unstructured, Tika) and some skip — so it is a distinct coverage point from a
body run. Rendered white and tiny so a human does not notice it in the header band.
Structural: the run is taggable.
"""

from __future__ import annotations

from docx.shared import Pt, RGBColor

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.docx.vectors._common import preserve_space, remove_tagged_elements


class HeaderFooterVector:
    name = "header_footer"
    format = "docx"
    marker_kind = "structural"
    description = "white 1pt run in the section header (separate XML part)"

    def _header_paragraph(self, doc):
        section = doc.sections[0]           # type: ignore[attr-defined]
        header = section.header
        header.is_linked_to_previous = False  # ensure a real header part exists
        return header.paragraphs[0]

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = self._header_paragraph(doc)
        run = para.add_run(payload)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        run.font.size = Pt(1)
        preserve_space(run)
        marker.tag_element(run._r, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        # Header runs live in the header part, not the body — walk each section's
        # header/footer XML.
        for section in doc.sections:        # type: ignore[attr-defined]
            for part in (section.header, section.footer):
                remove_tagged_elements(part._element, marker, self.name)


register(HeaderFooterVector())
