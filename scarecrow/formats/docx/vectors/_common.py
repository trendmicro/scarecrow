"""Shared helpers for DOCX structural vectors.

Several vectors insert a tagged run (or other element) and clean it the same way:
remove every element in the body carrying this vector's marker. Factoring that
here keeps each vector focused on its own hiding mechanism.
"""

from __future__ import annotations

from docx.oxml.ns import qn

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def preserve_space(run) -> None:
    """Keep leading/trailing whitespace in a run's text verbatim."""
    t = run._r.find(qn("w:t"))
    if t is not None:
        t.set(qn("xml:space"), "preserve")


def remove_tagged_elements(container_el, marker, vector_name: str,
                           local_name: str = "r") -> int:
    """Remove every `w:<local_name>` element under `container_el` tagged by this
    vector's marker. Returns the count removed."""
    removed = 0
    for el in container_el.findall(f".//{{{_W}}}{local_name}"):
        if el.get(marker.tag_attr) is not None and \
           el.get(marker.vector_attr) == vector_name:
            el.getparent().remove(el)
            removed += 1
    return removed
