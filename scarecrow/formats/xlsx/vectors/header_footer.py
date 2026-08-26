"""XLSX page-header vector (structural).

Puts the payload in the sheet's page header (the ``&L`` left section of
``<oddHeader>``). Headers/footers are printed text: absent from Excel's Normal
view, shown only in Page Layout view and Print Preview. openpyxl and Apache Tika
both extract header/footer text. A distinct channel from the cell grid.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.xlsx.vectors._common import record


class HeaderFooterVector:
    name = "header_footer"
    format = "xlsx"
    marker_kind = "structural"
    description = "payload in the page header (printed-only; not in Normal view)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        ws = doc.worksheets[0]                   # type: ignore[attr-defined]
        prev = ws.oddHeader.left.text or ""
        ws.oddHeader.left.text = payload
        record(marker, self.name, f"{ws.title}!oddHeader.left", payload, prev)

    def clean(self, doc: object, marker: Marker) -> None:
        return

    def clean_from_sidecar(self, doc: object, entry: dict) -> None:
        sheet = entry["location"].split("!", 1)[0]
        ws = doc[sheet]                          # type: ignore[index]
        ws.oddHeader.left.text = entry.get("previous") or None


register(HeaderFooterVector())
