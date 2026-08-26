"""The Vector plugin interface.

Every injection technique in Scarecrow is a Vector: a small plugin that knows how
to (a) apply a payload to a file using one hiding technique, and (b) later clean
that technique back out. Keeping each technique behind this uniform interface is
what lets `list-vectors`, `--vectors`, `--random`, `inspect`, and the per-vector
effectiveness benchmark all work without special-casing individual techniques.

Slice 1 ships exactly one Vector (the DOCX hidden run). The protocol and registry
exist from the start so later slices only add plugins, never rewire the core.
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

from scarecrow.core.marker import Marker

Format = Literal["docx", "xlsx", "pptx"]

# How a vector's payload is marked for later removal (see core/marker.py):
#   "structural" — payload lives in an element we can tag with a private sc:
#                  attribute (invisible to text extractors). clean() finds the tag.
#   "text-value" — the payload string *is* the extracted text, so an inline tag
#                  would be visible to the LLM; these are recorded in a sidecar.
MarkerKind = Literal["structural", "text-value"]


@runtime_checkable
class Vector(Protocol):
    """One injection technique for one file format."""

    name: str
    format: Format
    marker_kind: MarkerKind
    description: str  # one-line human summary, shown by `list-vectors`

    # Whether `protect --random` includes this vector by default. A vector may set
    # this False to stay in the library (selectable via --vectors) but be excluded
    # from the default posture — e.g. a channel the effectiveness experiment showed
    # no current model acts on, kept for research but not shipped as protection.
    # Absent attribute is treated as True (see default_random()).
    default_random: bool

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        """Insert `payload` into `doc` using this technique, tagged via `marker`."""
        ...

    def clean(self, doc: object, marker: Marker) -> None:
        """Remove everything this technique inserted, identified via `marker`."""
        ...


def default_random(vector: Vector) -> bool:
    """True if `--random` should include this vector (default when unset)."""
    return getattr(vector, "default_random", True)


# --- Registry ------------------------------------------------------------------
# Vectors register themselves at import time. The CLI imports the format packages
# (which import their vectors), populating this registry; list-vectors / --vectors
# / --random then read it. A plain module-level dict keeps discovery explicit and
# debuggable — no entry-point magic.

# Keyed on (format, name): the same technique name (e.g. "white_text",
# "core_props") legitimately exists in more than one format, so name alone is not
# unique across the whole tool.
_REGISTRY: dict[tuple[str, str], Vector] = {}


def register(vector: Vector) -> Vector:
    """Register a vector instance. Raises on duplicate (format, name)."""
    key = (vector.format, vector.name)
    if key in _REGISTRY:
        raise ValueError(f"duplicate vector: {vector.format}/{vector.name}")
    _REGISTRY[key] = vector
    return vector


def get(name: str, fmt: Format | None = None) -> Vector:
    """Look up a vector by name, optionally scoped to a format.

    If `fmt` is given, returns that format's vector. Without `fmt`, returns the
    sole match if the name is unique across formats, else raises (ambiguous)."""
    if fmt is not None:
        try:
            return _REGISTRY[(fmt, name)]
        except KeyError:
            raise KeyError(f"unknown vector: {fmt}/{name}") from None
    matches = [v for (f, n), v in _REGISTRY.items() if n == name]
    if not matches:
        raise KeyError(f"unknown vector: {name!r}")
    if len(matches) > 1:
        fmts = ", ".join(sorted(v.format for v in matches))
        raise KeyError(f"ambiguous vector {name!r} (in {fmts}); pass a format")
    return matches[0]


def all_vectors(fmt: Format | None = None) -> list[Vector]:
    """All registered vectors, optionally filtered to one format."""
    vs = list(_REGISTRY.values())
    if fmt is not None:
        vs = [v for v in vs if v.format == fmt]
    return vs


def default_vectors(fmt: Format | None = None) -> list[Vector]:
    """The default protection set that ``--all`` applies: every vector minus those
    opting out of the default posture (default_random=False, i.e. the research-only
    in-text encoding vectors). ``--vectors`` can still select the excluded ones."""
    return [v for v in all_vectors(fmt) if default_random(v)]


# Back-compat alias: the set used to be reached via `--random` / random_vectors.
random_vectors = default_vectors
