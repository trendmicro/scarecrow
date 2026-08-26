"""XLSX very-hidden-sheet vector (flagship).

Adds a whole worksheet carrying the payload and sets its ``state="veryHidden"``.
A veryHidden sheet appears in neither the tab bar nor Excel's Format > Sheet >
Unhide dialog (only VBA or direct XML editing reveals it), so it is effectively
invisible to a user. Every common spreadsheet-ingestion path reads it anyway:
openpyxl (`wb.worksheets`), pandas (`sheet_name=None`), and markitdown all return
veryHidden sheets without filtering. A whole sheet gives ample payload capacity.

Reversal is sidecar-driven: apply records the sheet name; clean removes that sheet.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.xlsx.vectors._common import SC_SHEET_PREFIX, record


class VeryHiddenSheetVector:
    name = "very_hidden_sheet"
    format = "xlsx"
    marker_kind = "structural"
    description = "a whole worksheet marked veryHidden (not even in Excel's Unhide menu)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        title = f"{SC_SHEET_PREFIX}{marker.run_id}"[:31]  # Excel caps sheet names at 31 chars
        ws = doc.create_sheet(title)             # type: ignore[attr-defined]
        ws["A1"] = payload
        ws.sheet_state = "veryHidden"
        record(marker, self.name, f"sheet:{title}", payload)

    def clean(self, doc: object, marker: Marker) -> None:
        return  # sidecar-driven

    def clean_from_sidecar(self, doc: object, entry: dict) -> None:
        title = entry["location"].split(":", 1)[1]
        if title in doc.sheetnames:              # type: ignore[attr-defined]
            del doc[title]                       # type: ignore[index]


register(VeryHiddenSheetVector())
