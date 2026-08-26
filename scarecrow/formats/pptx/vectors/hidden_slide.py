"""PPTX hidden-slide vector (structural).

Adds a whole slide carrying the payload and marks it ``show="0"`` on the ``<p:sld>``
element, so PowerPoint skips it during F5 slideshow playback (it appears only as a
struck-through thumbnail in the editing view). Every extractor walks ``ppt/slides/``
without checking ``show``, so the payload is read. Useful when the payload is large:
a full slide's worth of capacity.

Structural: we tag a shape on the hidden slide via its ``<p:cNvPr>``; clean() finds
the tagged shape, walks up to its owning slide, and drops the slide from the
presentation (slide list entry, relationship, and part).
"""

from __future__ import annotations

from pptx.util import Emu

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.pptx.vectors._common import qn_p, cNvPr_of, tag_shape


class HiddenSlideVector:
    name = "hidden_slide"
    format = "pptx"
    marker_kind = "structural"
    description = "a full slide marked show=0 (skipped in slideshow, read by extractors)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        # Add a blank slide (layout 6 is "Blank" in the default template).
        layout = doc.slide_layouts[6]             # type: ignore[attr-defined]
        slide = doc.slides.add_slide(layout)
        box = slide.shapes.add_textbox(Emu(0), Emu(0), Emu(4572000), Emu(2743200))
        box.text_frame.text = payload
        slide._element.set("show", "0")           # <p:sld show="0">
        tag_shape(box, marker, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        # Find slides that carry a shape tagged by this vector and remove them whole.
        for slide in list(doc.slides):            # type: ignore[attr-defined]
            tree = slide.shapes._spTree
            marked = any(
                c.get(marker.tag_attr) is not None and c.get(marker.vector_attr) == self.name
                for c in tree.findall(f".//{qn_p('cNvPr')}"))
            if marked:
                _drop_slide(doc, slide)


def _drop_slide(doc, slide) -> None:
    """Remove `slide` from the presentation: slide-list entry, relationship, part."""
    prs = doc  # a Presentation
    sldIdLst = prs.slides._sldIdLst
    rId = None
    for sldId in list(sldIdLst):
        # each <p:sldId> has r:id pointing at the slide part
        rid = sldId.get(qn_r("id"))
        # match by resolving the relationship to this slide's part
        if prs.part.rels[rid].target_part is slide.part:
            rId = rid
            sldIdLst.remove(sldId)
            break
    if rId is not None:
        prs.part.rels.pop(rId)  # _Relationships has no __delitem__; pop drops it


def qn_r(local: str) -> str:
    return f"{{http://schemas.openxmlformats.org/officeDocument/2006/relationships}}{local}"


register(HiddenSlideVector())
