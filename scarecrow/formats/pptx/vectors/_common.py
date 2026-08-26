"""Shared helpers for PPTX structural vectors.

PPTX text lives in the DrawingML text model: ``<a:t>`` runs inside ``<a:p>``
paragraphs inside ``<p:txBody>`` inside ``<p:sp>`` shapes — the same model is used
on slides AND in speaker notes, so vectors can reuse this machinery. Shape geometry
is ``<p:spPr><a:xfrm><a:off x= y=/><a:ext cx= cy=/></a:xfrm>`` in EMU (914400 per
inch); a negative offset pushes a shape off the visible slide canvas.

The ``sc:`` marker (a private-namespace attribute invisible to text extractors) is
set on the shape's ``<p:cNvPr>`` element, which every ``<p:sp>`` carries. clean()
finds shapes by that marker and removes them.
"""

from __future__ import annotations

from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor

# DrawingML + PresentationML namespaces (the two we touch).
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"


def qn_a(local: str) -> str:
    return f"{{{A}}}{local}"


def qn_p(local: str) -> str:
    return f"{{{P}}}{local}"


def cNvPr_of(shape) -> object:
    """The <p:cNvPr> element of a shape — where we hang the sc: marker + alt-text.

    Present on every shape kind (sp / pic / graphicFrame / grpSp)."""
    return shape._element.find(f".//{qn_p('cNvPr')}")


def tag_shape(shape, marker, vector_name: str) -> None:
    """Attach this run's sc: marker to a shape (via its cNvPr) so clean() finds it."""
    cnv = cNvPr_of(shape)
    if cnv is not None:
        cnv.set(marker.tag_attr, marker.run_id)
        cnv.set(marker.vector_attr, vector_name)


def add_offslide_textbox(slide, payload: str, off_emu: int = -9144000):
    """Add a text box to `slide` positioned off the visible canvas, return the shape.

    Shared by several structural vectors that then adjust formatting/position."""
    box = slide.shapes.add_textbox(Emu(off_emu), Emu(off_emu), Emu(914400), Emu(457200))
    box.text_frame.text = payload
    return box


def remove_tagged_shapes(slide, marker, vector_name: str) -> int:
    """Remove every shape on `slide` tagged by this vector's marker. Returns count."""
    removed = 0
    tree = slide.shapes._spTree
    for cnv in list(tree.findall(f".//{qn_p('cNvPr')}")):
        if cnv.get(marker.tag_attr) is not None and cnv.get(marker.vector_attr) == vector_name:
            # cNvPr -> nvSpPr (or nvPicPr...) -> the shape element (sp/pic/...)
            shape_el = cnv.getparent().getparent()
            if shape_el is not None and shape_el.getparent() is not None:
                shape_el.getparent().remove(shape_el)
                removed += 1
    return removed
