"""Reverse operations for XLSX — `clean` and `inspect`.

Unlike DOCX/PPTX, every XLSX vector is reversed from the sidecar (openpyxl
reserializes the whole workbook on save, so an inline ``sc:`` marker would not
survive; see vectors/_common.py). So both inspect and clean work off the
``*.scarecrow.json`` sidecar written next to the protected file.

`inspect` reports the recorded injections. `clean` opens the workbook, calls each
recorded vector's ``clean_from_sidecar`` to undo its change, and saves. It restores
structural equivalence, not byte-equivalence (openpyxl reserializes).
"""

from __future__ import annotations

from dataclasses import dataclass

from openpyxl import load_workbook

from scarecrow.core.marker import read_sidecar


@dataclass
class Injection:
    vector: str
    run_id: str
    text: str
    where: str            # "sidecar:<location>"


def inspect_xlsx(path: str) -> list[Injection]:
    """Return the Scarecrow injections found in `path` (from the sidecar). No writes."""
    out: list[Injection] = []
    for entry in read_sidecar(path):
        out.append(Injection(
            vector=entry.get("vector", "?"),
            run_id=entry.get("run_id", "?"),
            text=entry.get("value", ""),
            where=f"sidecar:{entry.get('location', '?')}",
        ))
    return out


def clean_xlsx(in_path: str, out_path: str) -> int:
    """Remove every Scarecrow injection recorded in the sidecar; write to `out_path`.

    Returns the number of injections removed.
    """
    from scarecrow import vector as _vec  # local import avoids a cycle at module load

    sidecar = read_sidecar(in_path)
    wb = load_workbook(in_path)
    for entry in sidecar:
        v = _vec.get(entry["vector"], "xlsx")
        restore = getattr(v, "clean_from_sidecar", None)
        if restore is not None:
            restore(wb, entry)
    wb.save(out_path)
    return len(sidecar)
