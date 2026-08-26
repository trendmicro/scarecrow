"""Reverse operations for DOCX — `clean` and `inspect` (Slices 2-3).

The counterpart to `protect`: find what Scarecrow injected and either report it
(`inspect`) or remove it (`clean`).

`inspect` works generically off the universal ``sc:`` marker: any structural
injection carries ``sc:tag`` (a per-run id) and ``sc:vector`` (which technique), so
discovery is "find every element with an sc:tag" wherever it lives (body, header,
footer, drawing). Text-value injections (sidecar) are reported from the sidecar
file.

`clean` delegates to each registered vector's ``clean(doc, marker)`` so a vector
that hides its payload somewhere unusual (a header part, a drawing, an image
attribute) removes it correctly, then restores any sidecar-recorded text-value
injections. It restores *structural* equivalence, not byte-equivalence — OOXML
reserializes non-deterministically, so a bytewise round-trip is not the goal.
"""

from __future__ import annotations

from dataclasses import dataclass

from docx import Document
from docx.oxml.ns import qn

from scarecrow.core.marker import TAG_ATTR, VECTOR_ATTR, Marker, read_sidecar

_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


@dataclass
class Injection:
    """One injected item found in a document (structural element or sidecar entry)."""
    vector: str
    run_id: str
    text: str
    where: str            # "body" / "header" / "footer" / "sidecar:<location>"


def _iter_marked(root):
    """Yield every element under `root` carrying an sc:tag marker."""
    for el in root.iter():
        if el.get(TAG_ATTR) is not None:
            yield el


def _element_text(el) -> str:
    return "".join(t.text or "" for t in el.iterfind(f".//{{{_W}}}t"))


def _structural_scopes(doc):
    """(label, xml-root) pairs to scan: the body plus every header/footer part."""
    yield "body", doc.element.body
    for section in doc.sections:
        yield "header", section.header._element
        yield "footer", section.footer._element


def inspect_docx(path: str) -> list[Injection]:
    """Return the Scarecrow injections found in `path` (structural + sidecar). No writes."""
    doc = Document(path)
    out: list[Injection] = []
    # body and header/footer roots do not overlap, so no cross-scope dedup is
    # needed. Materialize each scope's marked elements into a list (holding
    # references) before building results — never key on id(), which lxml can
    # reuse for GC'd elements mid-traversal.
    for label, root in _structural_scopes(doc):
        for el in list(_iter_marked(root)):
            out.append(Injection(
                vector=el.get(VECTOR_ATTR) or "?",
                run_id=el.get(TAG_ATTR) or "?",
                text=_element_text(el),
                where=label,
            ))
    for entry in read_sidecar(path):
        out.append(Injection(
            vector=entry.get("vector", "?"),
            run_id=entry.get("run_id", "?"),
            text=entry.get("value", ""),
            where=f"sidecar:{entry.get('location', '?')}",
        ))
    return out


def clean_docx(in_path: str, out_path: str) -> int:
    """Remove every Scarecrow injection from `in_path`, write the result to `out_path`.

    Returns the number of injections removed (structural elements + sidecar entries).
    Delegates structural removal to each registered DOCX vector's clean(), then
    restores text-value injections from the sidecar.
    """
    from scarecrow import vector as _vec  # local import avoids a cycle at module load

    doc = Document(in_path)

    # Count structural injections before removal (across body + headers/footers).
    before = sum(1 for _, root in _structural_scopes(doc) for _ in _iter_marked(root))

    # A blank marker carries the same tag_attr/vector_attr constants; that is all a
    # vector's clean() needs to locate its tagged elements.
    marker = Marker()
    for v in _vec.all_vectors("docx"):
        v.clean(doc, marker)

    # Prune paragraphs left empty by structural removals (body only; header/footer
    # paragraphs are always present by design).
    body = doc.element.body
    for p in list(body.iter(qn("w:p"))):
        if p.find(f".//{{{_W}}}r") is None and p.getparent() is not None:
            # only prune paragraphs with no text at all (don't touch real content)
            if not (p.text or "").strip():
                p.getparent().remove(p)

    # Restore text-value (sidecar) injections.
    sidecar = read_sidecar(in_path)
    for entry in sidecar:
        v = _vec.get(entry["vector"], "docx")
        restore = getattr(v, "clean_from_sidecar", None)
        if restore is not None:
            restore(doc, entry)

    doc.save(out_path)
    return before + len(sidecar)
