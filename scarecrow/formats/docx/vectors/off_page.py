"""DOCX off-page text-box vector.

Inserts a floating text box anchored off the page (negative offset, one inch past
the top-left corner) containing the payload. The text is never rendered — it is
outside the page bounds — but extractors that descend into text-box content
(Apache Tika, markitdown, naive XML readers) still pull it out. This reaches a
*different* subset of extractors than the body-run vectors, which is why it is
worth having as a separate technique.

Structural: the whole `<w:drawing>` is tagged, so the generic marker-based clean
removes it. Note the payload lives in `txbxContent`, which python-docx's
`paragraphs.text` does not descend into — so this vector does not reach
python-docx-based pipelines (an honest coverage limit, recorded in tests).
"""

from __future__ import annotations

from docx.oxml.ns import qn
from lxml import etree

from scarecrow.core.marker import Marker
from scarecrow.vector import register

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# One inch (914400 EMU) off the top-left corner of the page — safely off-canvas.
_OFF = -914400

_DRAWING_TMPL = """<w:drawing xmlns:w="{w}"
  xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
  xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
  xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
  <wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0"
             behindDoc="1" locked="0" layoutInCell="1" allowOverlap="1">
    <wp:simplePos x="0" y="0"/>
    <wp:positionH relativeFrom="page"><wp:posOffset>{off}</wp:posOffset></wp:positionH>
    <wp:positionV relativeFrom="page"><wp:posOffset>{off}</wp:posOffset></wp:positionV>
    <wp:extent cx="900000" cy="450000"/>
    <wp:effectExtent l="0" t="0" r="0" b="0"/>
    <wp:wrapNone/>
    <wp:docPr id="1" name="sc-offpage"/>
    <a:graphic><a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">
      <wps:wsp>
        <wps:cNvSpPr txBox="1"/>
        <wps:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="900000" cy="450000"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></wps:spPr>
        <wps:txbx><w:txbxContent><w:p><w:r><w:t xml:space="preserve">{payload}</w:t></w:r></w:p></w:txbxContent></wps:txbx>
        <wps:bodyPr/>
      </wps:wsp>
    </a:graphicData></a:graphic>
  </wp:anchor>
</w:drawing>"""


def _xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class OffPageVector:
    name = "off_page"
    format = "docx"
    marker_kind = "structural"
    description = "off-canvas floating text box (reaches Tika/markitdown, not python-docx)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        run = para.add_run()
        drawing = etree.fromstring(
            _DRAWING_TMPL.format(w=_W, off=_OFF, payload=_xml_escape(payload)))
        # Tag the drawing so the generic marker-based clean removes the whole box.
        drawing.set(marker.tag_attr, marker.run_id)
        drawing.set(marker.vector_attr, self.name)
        run._r.append(drawing)

    def clean(self, doc: object, marker: Marker) -> None:
        body = doc.element.body                  # type: ignore[attr-defined]
        for dr in body.findall(f".//{{{_W}}}drawing"):
            if dr.get(marker.tag_attr) is not None and \
               dr.get(marker.vector_attr) == self.name:
                # remove the drawing and, if its run is now empty, the run too
                run = dr.getparent()
                dr.getparent().remove(dr)
                if run is not None and run.find(f".//{{{_W}}}t") is None:
                    run.getparent().remove(run)


register(OffPageVector())
