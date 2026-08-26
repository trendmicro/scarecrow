"""XLSX cell-comment vector (structural).

Attaches the payload as a legacy cell comment (note) on a cell. Comments show only
as a small indicator and on hover, never in the normal cell view. openpyxl
(`cell.comment`) and Apache Tika both extract comment text. A separate part of the
file from the cell grid, so a distinct extractor-coverage point.
"""

from __future__ import annotations

from openpyxl.comments import Comment

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.xlsx.vectors._common import CELLS, record

_CELL = CELLS["comment"]  # a dedicated off-canvas cell (comment sits on it)


class CommentVector:
    name = "comment"
    format = "xlsx"
    marker_kind = "structural"
    description = "payload in a cell comment/note (shown only on hover)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        ws = doc.worksheets[0]                   # type: ignore[attr-defined]
        ws[_CELL].comment = Comment(payload, "sc")
        record(marker, self.name, f"{ws.title}!{_CELL}", payload)

    def clean(self, doc: object, marker: Marker) -> None:
        return

    def clean_from_sidecar(self, doc: object, entry: dict) -> None:
        sheet, ref = entry["location"].split("!", 1)
        ws = doc[sheet]                          # type: ignore[index]
        ws[ref].comment = None


register(CommentVector())
