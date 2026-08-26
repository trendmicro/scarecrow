"""DOCX comment vector.

Puts the payload in a Word comment (`word/comments.xml`). Comments are not shown
in the printed/read view, but several extractors surface them (Tika, markitdown,
pandoc with --track-changes=all). A separate XML part, so it is a distinct
extractor-coverage point from body runs.

Structural: the comment element and its anchoring run are tagged, so clean removes
them. Note: the comment's text is in comments.xml, not the body, so the generic
body-only walk would miss it — this vector's own clean() handles the comment part.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


class CommentVector:
    name = "comments"
    format = "docx"
    marker_kind = "structural"
    description = "payload in a Word comment (separate comments.xml part)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        # Anchor the comment on a zero-width run so nothing visible is added.
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        anchor = para.add_run("​")          # zero-width space, invisible
        comment = doc.add_comment(               # type: ignore[attr-defined]
            runs=[anchor], text=payload, author="sc", initials="sc")
        # Tag the anchoring run and the comment element for cleanup.
        marker.tag_element(anchor._r, self.name)
        try:
            marker.tag_element(comment._comment, self.name)
        except Exception:
            pass  # comment object shape varies; the anchor tag is enough to find it

    def clean(self, doc: object, marker: Marker) -> None:
        # Remove tagged anchor runs from the body.
        body = doc.element.body                  # type: ignore[attr-defined]
        for r in body.findall(f".//{{{_W}}}r"):
            if r.get(marker.tag_attr) is not None and r.get(marker.vector_attr) == self.name:
                r.getparent().remove(r)
        # Remove our comments from the comments part (identified by author "sc").
        # python-docx exposes it at doc.part._comments_part.element.
        part = getattr(doc.part, "_comments_part", None)  # type: ignore[attr-defined]
        el = getattr(part, "element", None) if part is not None else None
        if el is not None:
            for c in list(el.findall(f".//{{{_W}}}comment")):
                if c.get(f"{{{_W}}}author") == "sc":
                    c.getparent().remove(c)


register(CommentVector())
