"""DOCX tracked-change deleted-text vector.

Inserts the payload as *deleted* text under a tracked change
(`<w:del><w:r><w:delText>...`). With "Show Markup" off — the default reading view
— it is invisible, but the text is still in the file. Extractors that surface
tracked changes (Tika opt-in, pandoc --track-changes=all, naive XML) pull it out.
python-docx's `.text` does NOT read `w:delText` (it only reads `w:t`), so this
reaches a different extractor subset than a body run — the point of having it.

Structural: the `<w:del>` element is tagged, so this vector's clean() removes it.
"""

from __future__ import annotations

from lxml import etree

from scarecrow.core.marker import Marker
from scarecrow.vector import register

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class TrackedDeleteVector:
    name = "tracked_delete"
    format = "docx"
    marker_kind = "structural"
    description = "payload as tracked-change deleted text (invisible with markup off)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        xml = (
            f'<w:del xmlns:w="{_W}" w:id="9001" w:author="sc" '
            f'w:date="2020-01-01T00:00:00Z">'
            f'<w:r><w:delText xml:space="preserve">{_xml_escape(payload)}</w:delText></w:r>'
            f'</w:del>'
        )
        el = etree.fromstring(xml)
        el.set(marker.tag_attr, marker.run_id)
        el.set(marker.vector_attr, self.name)
        para._p.append(el)

    def clean(self, doc: object, marker: Marker) -> None:
        body = doc.element.body                  # type: ignore[attr-defined]
        for el in body.findall(f".//{{{_W}}}del"):
            if el.get(marker.tag_attr) is not None and el.get(marker.vector_attr) == self.name:
                el.getparent().remove(el)


register(TrackedDeleteVector())
