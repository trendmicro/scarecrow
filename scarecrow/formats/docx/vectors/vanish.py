"""DOCX hidden-run vector (``w:vanish``) — Scarecrow's flagship technique.

A run marked with the OOXML ``<w:vanish/>`` property is present in the document's
text stream (so every mainstream extractor — python-docx, docx2txt, mammoth,
markitdown, unstructured, LibreOffice text export — pulls it out and feeds it to
the LLM) but is not rendered in Word. We belt-and-suspenders it with white colour
and 1pt size so it also survives a pipeline that happens to filter on only one of
those properties.

marker_kind is "structural": the payload lives in a run element we can tag with a
private sc: attribute, so it is invisible to the LLM and removable by clean().
"""

from __future__ import annotations

from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from scarecrow.core.marker import Marker
from scarecrow.vector import register


class VanishVector:
    name = "vanish"
    format = "docx"
    marker_kind = "structural"
    description = "hidden run (w:vanish + white + 1pt) at the top of the body"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        """Insert the payload as a hidden run at the very top of the body.

        Placing it first means it lands early in the extracted text stream, before
        the real content — which several studies find raises compliance.
        """
        # A fresh paragraph, moved to the front of the body.
        para = doc.add_paragraph()          # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)  # type: ignore[attr-defined]

        run = para.add_run(payload)
        run.font.hidden = True                          # <w:vanish/>
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)  # white
        run.font.size = Pt(1)                           # 1pt (sz val=2)

        # Preserve any leading/trailing whitespace in the payload verbatim.
        t = run._r.find(qn("w:t"))
        if t is not None:
            t.set(qn("xml:space"), "preserve")

        # Tag the run so clean()/inspect() can find exactly what we inserted.
        marker.tag_element(run._r, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        """Remove every run this vector tagged (used by Slice 2's `clean`)."""
        body = doc.element.body  # type: ignore[attr-defined]
        for run_el in body.findall(f".//{{{_W}}}r"):
            if run_el.get(marker.tag_attr) is not None and \
               run_el.get(marker.vector_attr) == self.name:
                run_el.getparent().remove(run_el)


_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Register the single instance at import time.
register(VanishVector())
