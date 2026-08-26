"""DOCX vectors. Importing this package registers every DOCX vector."""

# Each import registers its vector at module load. Order here is the order
# `list-vectors` and `--all` (default set) see them.
#
# Two families:
#   structural "hide a separate element" — vanish, white_text, header_footer,
#     off_page, alt_text, comments, tracked_delete; plus the text-value core_props.
#   in-text encoding "poison the text stream" — unicode_tags, zero_width.
from scarecrow.formats.docx.vectors import vanish          # noqa: F401
from scarecrow.formats.docx.vectors import white_text      # noqa: F401
from scarecrow.formats.docx.vectors import header_footer   # noqa: F401
from scarecrow.formats.docx.vectors import off_page        # noqa: F401
from scarecrow.formats.docx.vectors import alt_text        # noqa: F401
from scarecrow.formats.docx.vectors import core_props      # noqa: F401
from scarecrow.formats.docx.vectors import unicode_tags    # noqa: F401
from scarecrow.formats.docx.vectors import zero_width      # noqa: F401
from scarecrow.formats.docx.vectors import comments        # noqa: F401
from scarecrow.formats.docx.vectors import tracked_delete  # noqa: F401
