"""XLSX blank-number-format vector (text-value / sidecar).

Writes the payload into a cell and applies the custom number format ``;;;`` — a
four-section format (positive;negative;zero;text) with every section empty, so
Excel renders the cell completely blank while the value stays in the file. Read
by every extractor path including pandas and markitdown (which return the raw cell
value, ignoring the display format), so it is one of the highest-reach vectors.

Text-value: the payload IS the cell value, so there is nowhere to hang an inline
marker. apply records a sidecar entry (cell + previous value + previous format);
clean restores them.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.xlsx.vectors._common import CELLS, record

_CELL = CELLS["semicolon_format"]  # a dedicated off-canvas cell


class SemicolonFormatVector:
    name = "semicolon_format"
    format = "xlsx"
    marker_kind = "text-value"
    description = "cell value hidden by the ;;; number format (present in file, blank in Excel)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        ws = doc.worksheets[0]                   # type: ignore[attr-defined]
        cell = ws[_CELL]
        prev_val = "" if cell.value is None else str(cell.value)
        prev_fmt = cell.number_format
        cell.value = payload
        cell.number_format = ";;;"
        # encode both previous value and format in the sidecar (pipe-joined)
        record(marker, self.name, f"{ws.title}!{_CELL}", payload, f"{prev_fmt}|{prev_val}")

    def clean(self, doc: object, marker: Marker) -> None:
        return

    def clean_from_sidecar(self, doc: object, entry: dict) -> None:
        sheet, ref = entry["location"].split("!", 1)
        ws = doc[sheet]                          # type: ignore[index]
        prev = entry.get("previous") or "|"
        fmt, val = prev.split("|", 1)
        ws[ref].value = val or None
        ws[ref].number_format = fmt or "General"


register(SemicolonFormatVector())
