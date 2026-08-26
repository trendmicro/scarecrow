"""Marker infrastructure — how Scarecrow tags what it injects, so `clean` can
find and remove it later.

Two marking channels:


  1. Structural: a private XML-namespace attribute ``sc:tag="<run id>"`` placed on
     the element a vector inserts. Because it is an attribute in a namespace no
     text extractor reads, it is invisible to an ingesting LLM, yet a later
     `clean` pass can locate every tagged element by XPath and delete it. Used by
     "structural" vectors (hidden runs, hidden sheets, off-slide shapes, alt
     text, ...).

  2. Sidecar (Slice 3): a ``<name>.scarecrow.json`` file recording entries for
     "text-value" vectors, where the payload string *is* the extracted text and
     so cannot carry an inline marker without the LLM seeing it (e.g. a document
     core property). A vector records what it wrote (which property / where, and
     the value) so `clean` can locate and remove it without any in-file tag.

A ``Marker`` instance carries the per-protect-run id used to tag elements, the
namespace constants, and the accumulating list of sidecar entries. One Marker is
created per `protect` invocation.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path

# Private namespace for Scarecrow's structural tags. Not an OOXML namespace, so
# Word ignores it and text extractors never surface it.
SC_NAMESPACE = "https://trendmicro.com/scarecrow"
SC_PREFIX = "sc"


def _qname(local: str) -> str:
    """Clark-notation qualified name for an sc: attribute, e.g. sc:tag."""
    return f"{{{SC_NAMESPACE}}}{local}"


# Pre-computed qualified attribute names used by vectors and by clean/inspect.
TAG_ATTR = _qname("tag")        # sc:tag="<run id>" — marks an injected element
VECTOR_ATTR = _qname("vector")  # sc:vector="<vector name>" — which technique tagged it


@dataclass
class Marker:
    """Identifies one protect run and tags/finds the elements it injected."""

    # Unique per protect invocation; ties all elements from one run together so a
    # future `clean` can target exactly this run's injections.
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])

    # Constants exposed for vectors that manipulate lxml directly.
    tag_attr: str = TAG_ATTR
    vector_attr: str = VECTOR_ATTR

    # Sidecar entries recorded by text-value vectors during apply(). Each entry
    # describes what was written so clean() can undo it (see record_sidecar).
    sidecar_entries: list[dict] = field(default_factory=list)

    def tag_element(self, element: object, vector_name: str) -> None:
        """Attach this run's marker to a raw lxml element (structural channel).

        `element` is an lxml element (e.g. a python-docx run's ``._r``). We set
        both sc:tag (the run id) and sc:vector (which technique placed it) so
        `inspect` can report per-vector and `clean` can be selective if needed.
        """
        element.set(self.tag_attr, self.run_id)  # type: ignore[attr-defined]
        element.set(self.vector_attr, vector_name)  # type: ignore[attr-defined]

    def record_sidecar(self, vector_name: str, location: str, value: str,
                       previous: str | None = None) -> None:
        """Record a text-value injection for the sidecar (non-structural channel).

        `location` identifies where the value was written (vector-specific, e.g. a
        core-property name like "subject"); `value` is what was injected; `previous`
        is the prior value so clean() can restore rather than just blank it.
        """
        self.sidecar_entries.append({
            "vector": vector_name, "location": location,
            "value": value, "previous": previous, "run_id": self.run_id,
        })


# --- Sidecar file I/O ----------------------------------------------------------
# The sidecar lives next to the protected file: foo.scarecrow.docx -> the sidecar
# path is derived by the CLI. Only written when there are text-value entries.

def sidecar_path_for(output_path: str) -> Path:
    """Sidecar path for a protected output file: foo.scarecrow.docx -> foo.scarecrow.json."""
    p = Path(output_path)
    return p.with_suffix(".json")


def write_sidecar(output_path: str, entries: list[dict]) -> Path | None:
    """Write the sidecar next to `output_path` if there are entries. Returns its path."""
    if not entries:
        return None
    sp = sidecar_path_for(output_path)
    json.dump({"scarecrow_sidecar": 1, "entries": entries},
              open(sp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    return sp


def read_sidecar(path: str) -> list[dict]:
    """Read sidecar entries for a protected file, or [] if none exists."""
    sp = sidecar_path_for(path)
    if not sp.exists():
        return []
    data = json.load(open(sp, encoding="utf-8"))
    return data.get("entries", [])
