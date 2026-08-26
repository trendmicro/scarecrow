"""PPTX vectors. Importing this package registers every PPTX vector.

Each import registers its vector at module load. Order here is the order
`list-vectors` and `--all` see them; the flagship (speaker_notes) leads.

Families mirror the DOCX library:
  structural / text-value "hide it somewhere invisible" — speaker_notes,
    white_text, tiny_font, off_slide, zero_size, alt_text, hidden_slide,
    core_props.
  in-text encoding "poison the text stream" — unicode_tags, zero_width
    (research-only; excluded from --all).
"""

from scarecrow.formats.pptx.vectors import speaker_notes   # noqa: F401  (flagship)
from scarecrow.formats.pptx.vectors import white_text      # noqa: F401
from scarecrow.formats.pptx.vectors import tiny_font       # noqa: F401
from scarecrow.formats.pptx.vectors import off_slide       # noqa: F401
from scarecrow.formats.pptx.vectors import zero_size       # noqa: F401
from scarecrow.formats.pptx.vectors import alt_text        # noqa: F401
from scarecrow.formats.pptx.vectors import hidden_slide    # noqa: F401
from scarecrow.formats.pptx.vectors import core_props      # noqa: F401
from scarecrow.formats.pptx.vectors import unicode_tags    # noqa: F401
from scarecrow.formats.pptx.vectors import zero_width      # noqa: F401
