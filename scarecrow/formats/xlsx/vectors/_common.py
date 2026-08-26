"""Shared helpers + marking model for XLSX vectors.

XLSX differs from DOCX/PPTX in how we mark injections. In those formats we hang a
private ``sc:`` attribute on the injected element and let ``clean`` find it by
XPath. openpyxl, however, does not expose a stable per-cell lxml element to tag,
and it fully reserializes the workbook on save, so an inline ``sc:`` attribute
would not survive a round-trip.

So every XLSX vector — structural and text-value alike — records a **sidecar**
entry describing exactly what it did (which sheet/cell/name it wrote, the value,
and the previous value where one existed). ``clean`` replays the sidecar in
reverse. This keeps reversibility robust without fighting openpyxl's serializer.
The ``location`` field is a vector-specific string the vector's own
``clean_from_sidecar`` knows how to parse.

Convention: a Scarecrow-added worksheet is named with this prefix so inspect/clean
can also recognize it structurally if a sidecar is ever missing.
"""

from __future__ import annotations

SC_SHEET_PREFIX = "_sc_"  # veryHidden payload sheets are named _sc_<runid>

# Each cell-based vector writes to its OWN cell far outside any plausible used
# range, so vectors never collide with real data or with each other. Column AZ
# (well past typical content) at a distinct high row per vector.
CELLS = {
    "semicolon_format": "AZ1000",
    "white_fill": "AZ1001",
    "hidden_row": "AZ1002",
    "hidden_col": "AZ1003",
    "comment": "AZ1004",
    "unicode_tags": "AZ1005",
    "zero_width": "AZ1006",
}


def record(marker, vector_name: str, location: str, value: str,
           previous: str | None = None) -> None:
    """Record an injection in the marker's sidecar (all XLSX vectors use this)."""
    marker.record_sidecar(vector_name, location, value, previous)
