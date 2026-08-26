"""DOCX image alt-text vector.

Inserts a 1x1 transparent image and puts the payload in its alt-text
(`<wp:docPr descr="...">`). Alt-text is never rendered visibly, but several
extractors and multimodal pipelines surface it (Tika, mammoth, pandoc). This is a
distinct coverage point: the payload rides on an image attribute, not a text run.

Structural: the drawing's `docPr` carries the marker; clean removes the whole
inline image (and its now-empty run).
"""

from __future__ import annotations

import io
import struct
import zlib

from docx.shared import Emu

from scarecrow.core.marker import Marker
from scarecrow.vector import register

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _tiny_png() -> bytes:
    """A minimal 1x1 transparent PNG so add_picture has something to embed."""
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0)
    idat = zlib.compress(b"\x00\x00\x00\x00\x00")
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


class AltTextVector:
    name = "alt_text"
    format = "docx"
    marker_kind = "structural"
    description = "payload in an inline image's alt-text (descr attribute)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        run = para.add_run()
        pic = run.add_picture(io.BytesIO(_tiny_png()), width=Emu(9525))  # 1px
        docpr = pic._inline.docPr
        docpr.set("descr", payload)
        # Tag the drawing (docPr's ancestor) so clean can find and remove it.
        marker.tag_element(docpr, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        body = doc.element.body                  # type: ignore[attr-defined]
        # docPr elements carry the marker; remove the enclosing run.
        for el in list(body.iter()):
            if el.get(marker.tag_attr) is not None and \
               el.get(marker.vector_attr) == self.name:
                run = el
                while run is not None and run.tag != f"{{{_W}}}r":
                    run = run.getparent()
                if run is not None and run.getparent() is not None:
                    run.getparent().remove(run)


register(AltTextVector())
