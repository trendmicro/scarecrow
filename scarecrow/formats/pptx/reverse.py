"""Reverse operations for PPTX — `clean` and `inspect`.

The PPTX counterpart to the DOCX reverse module. `inspect` finds structural
injections generically off the `sc:` marker (set on each injected shape's
`<p:cNvPr>`), scanning every slide's shape tree, and reports text-value injections
from the sidecar. `clean` delegates to each registered PPTX vector's `clean(doc,
marker)` (so a vector that hides its payload in an unusual place removes it
correctly) then restores sidecar-recorded text-value injections.

Restores structural equivalence, not byte-equivalence (OOXML reserializes
non-deterministically), matching the DOCX behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass

from pptx import Presentation

from scarecrow.core.marker import TAG_ATTR, VECTOR_ATTR, Marker, read_sidecar
from scarecrow.formats.pptx.vectors._common import qn_a, qn_p


@dataclass
class Injection:
    vector: str
    run_id: str
    text: str
    where: str            # "slide:N" / "sidecar:<location>"


def _shape_text(shape_el) -> str:
    """Concatenate the <a:t> run text under a shape element (may be empty, e.g. for
    an alt-text-only shape whose payload lives in the descr attribute)."""
    parts = ["".join(t.text or "" for t in shape_el.iterfind(f".//{qn_a('t')}"))]
    # include alt-text (descr) so inspect surfaces alt_text-vector payloads
    cnv = shape_el.find(f".//{qn_p('cNvPr')}")
    if cnv is not None and cnv.get("descr"):
        parts.append(f"[descr] {cnv.get('descr')}")
    return " ".join(p for p in parts if p)


def _marked_shapes(prs):
    """Yield (slide_index, cNvPr_element, owning_shape_element) for every tagged shape,
    across all slides (a hidden slide is still in prs.slides)."""
    for i, slide in enumerate(prs.slides):
        tree = slide.shapes._spTree
        for cnv in tree.findall(f".//{qn_p('cNvPr')}"):
            if cnv.get(TAG_ATTR) is not None:
                shape_el = cnv.getparent().getparent()  # cNvPr -> nvSpPr -> sp
                yield i, cnv, shape_el


def inspect_pptx(path: str) -> list[Injection]:
    """Return the Scarecrow injections found in `path` (structural + sidecar). No writes."""
    prs = Presentation(path)
    out: list[Injection] = []
    for i, cnv, shape_el in _marked_shapes(prs):
        out.append(Injection(
            vector=cnv.get(VECTOR_ATTR) or "?",
            run_id=cnv.get(TAG_ATTR) or "?",
            text=_shape_text(shape_el),
            where=f"slide:{i}",
        ))
    for entry in read_sidecar(path):
        out.append(Injection(
            vector=entry.get("vector", "?"),
            run_id=entry.get("run_id", "?"),
            text=entry.get("value", ""),
            where=f"sidecar:{entry.get('location', '?')}",
        ))
    return out


def clean_pptx(in_path: str, out_path: str) -> int:
    """Remove every Scarecrow injection from `in_path`, write the result to `out_path`.

    Returns the number of injections removed (structural shapes + sidecar entries).
    Delegates structural removal to each registered PPTX vector's clean(), then
    restores text-value injections from the sidecar.
    """
    from scarecrow import vector as _vec  # local import avoids a cycle at module load

    prs = Presentation(in_path)

    # Count structural injections (tagged shapes across all slides) before removal.
    before = sum(1 for _ in _marked_shapes(prs))

    marker = Marker()
    for v in _vec.all_vectors("pptx"):
        v.clean(prs, marker)

    sidecar = read_sidecar(in_path)
    for entry in sidecar:
        v = _vec.get(entry["vector"], "pptx")
        restore = getattr(v, "clean_from_sidecar", None)
        if restore is not None:
            restore(prs, entry)

    prs.save(out_path)
    return before + len(sidecar)
