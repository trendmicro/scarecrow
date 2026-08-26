"""DOCX invisible-Unicode Tags-block vector.

Encodes the payload into the Unicode Tags block (U+E0000-U+E007F) and adds it as
a run in the body. The characters render as nothing, so the run is invisible even
though it is normal (not `w:vanish`, not white) — the invisibility is in the
codepoints. Every extractor passes the codepoints through to the model, and some
model families (Anthropic in particular) decode Tags-block instructions.

A different *family* from the structural vectors: the instruction rides in the
text stream itself, not a hidden element. Structural: the run is taggable, so the
generic marker-based clean removes it.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register
from scarecrow.formats.docx.vectors._common import preserve_space, remove_tagged_elements
from scarecrow.formats.docx.vectors._encodings import encode_tags


class UnicodeTagsVector:
    name = "unicode_tags"
    format = "docx"
    marker_kind = "structural"
    description = "payload encoded in the invisible Unicode Tags block, in the text stream"
    # Excluded from `--all`: the per-vector experiment found no model
    # decoded this encoding (1/14, no canary echoes). Kept in the library for
    # research; select explicitly with `--vectors unicode_tags`.
    default_random = False

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        para = doc.add_paragraph()               # type: ignore[attr-defined]
        doc.element.body.insert(0, para._p)      # type: ignore[attr-defined]
        run = para.add_run(encode_tags(payload))
        preserve_space(run)
        marker.tag_element(run._r, self.name)

    def clean(self, doc: object, marker: Marker) -> None:
        remove_tagged_elements(doc.element.body, marker, self.name)  # type: ignore[attr-defined]


register(UnicodeTagsVector())
