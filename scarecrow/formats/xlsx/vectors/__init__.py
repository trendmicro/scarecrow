"""XLSX vectors. Importing this package registers every XLSX vector.

Order here is the order `list-vectors` and `--all` see them; the flagship
(very_hidden_sheet) leads. Eight vectors, all structural or text-value:
  very_hidden_sheet, semicolon_format, white_fill, hidden_row, hidden_col,
  header_footer, comment, core_props.

Note: unlike DOCX/PPTX, XLSX has NO in-text encoding vectors (unicode_tags /
zero_width). openpyxl silently strips the Unicode Tags-block and zero-width
codepoints on save, so they cannot round-trip; and the per-vector experiment
already found no model decodes them, so they are not worth a fragile
raw-XML workaround. XLSX therefore ships 8 vectors where DOCX/PPTX ship 10.
"""

from scarecrow.formats.xlsx.vectors import very_hidden_sheet  # noqa: F401  (flagship)
from scarecrow.formats.xlsx.vectors import semicolon_format   # noqa: F401
from scarecrow.formats.xlsx.vectors import white_fill         # noqa: F401
from scarecrow.formats.xlsx.vectors import hidden_row         # noqa: F401
from scarecrow.formats.xlsx.vectors import hidden_col         # noqa: F401
from scarecrow.formats.xlsx.vectors import header_footer      # noqa: F401
from scarecrow.formats.xlsx.vectors import comment            # noqa: F401
from scarecrow.formats.xlsx.vectors import core_props         # noqa: F401
