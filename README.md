# Scarecrow

[![CI](https://github.com/trendmicro/scarecrow/actions/workflows/ci.yml/badge.svg)](https://github.com/trendmicro/scarecrow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Insert prompt injections into Microsoft Office files so a human reads them
normally, but an AI that ingests the file (via text extraction) is derailed.

Defensive framing: the file's owner runs `scarecrow protect report.docx` to make
the file resistant to unauthorized AI ingestion — for example, an attacker who
exfiltrates it and dumps it into ChatGPT to speed-read.

- **DOCX**, **PPTX**, and **XLSX** are all supported (`protect`/`clean`/`inspect`),
  each with its own vector library and all three modes
  (`refuse`/`corrupt`/`canary`).

## License

This project is released under the [MIT License](LICENSE).

## How it works

A `.docx`/`.xlsx`/`.pptx` file is a ZIP of XML. Text extractors read the whole
XML (everything present in the markup); the app that renders the file for a human
shows only what draws to the screen. Scarecrow puts an instruction in that gap:
text that is present in the file and pulled out by an AI's extraction path, yet
invisible to a person opening the document. The instruction tells an ingesting AI
to stop and refuse to process the file.

Each hiding technique is a **vector** (e.g. the DOCX hidden-run `w:vanish`
vector). What the injection asks the AI to do is a **mode**: `refuse` (decline to
process), `corrupt` (report the figures as decoys / return plausible-but-wrong
output), or `canary` (fetch a caller-supplied beacon URL, which doubles as breach
detection). Everything Scarecrow injects is tagged so it can be cleanly removed
again.

## Install

```
pipx install .        # or: pip install -e .
```

Requires Python 3.11+.

## Usage

```
scarecrow protect report.docx                    # default vector (docx: vanish), refuse mode
scarecrow protect deck.pptx                       # default vector (pptx: speaker_notes)
scarecrow protect book.xlsx                       # default vector (xlsx: very_hidden_sheet)
scarecrow protect report.docx --vectors vanish,alt_text   # pick specific vectors
scarecrow protect deck.pptx --all                 # apply the whole default vector set
scarecrow protect report.docx --mode corrupt     # report figures as decoys instead of refusing
scarecrow protect report.docx --mode canary --canary-url https://you.example/px.png  # beacon on ingestion
scarecrow protect report.docx --output out.docx
scarecrow protect report.docx --in-place         # overwrite the input (opt-in)

scarecrow list-vectors                           # what techniques are available
scarecrow list-vectors --format pptx --json

scarecrow inspect deck.scarecrow.pptx            # report what's been injected (+ --json)
scarecrow clean deck.scarecrow.pptx              # -> deck.scarecrow.cleaned.pptx (or --in-place)
```

**DOCX, PPTX, and XLSX** are all supported; the format is chosen by the file
extension. Each ships its own vector library (run `list-vectors --format xlsx`).
DOCX and PPTX have ten vectors; XLSX has eight (see below).

The original file is never modified unless you pass `--in-place`; by default a new
`*.scarecrow.docx` (protect) or `*.cleaned.docx` (clean) is written next to it.
`inspect` never modifies the file. `clean` reverses protection by removing every
element Scarecrow tagged (and restoring any metadata it changed via the sidecar),
restoring the document to structural equivalence with the original.

**Vectors** are the individual hiding techniques; run `list-vectors` to see them.
DOCX ships **ten**, in two families:

- *Structural* — hide the payload in a separate, tagged element `clean` can delete:
  `vanish`, `white_text`, `header_footer`, `off_page` (text box), `alt_text`
  (image alt-text), `comments`, `tracked_delete` (tracked-change deleted text).
- *In-text encoding* — carry the instruction invisibly inside the visible text
  stream: `unicode_tags` (Unicode Tags block) and `zero_width` (zero-width binary).
  These are **research-only**: the per-vector experiment found no
  current model decodes them (1/14 and 0/14 protected, no beacon echoes), so they
  are excluded from `--all` but stay in the library for further study — select
  them explicitly with `--vectors unicode_tags,zero_width`.

One vector (`core_props`, a document property) is *text-value* — its payload is a
visible field value, so it is recorded in a `*.scarecrow.json` **sidecar** next to
the protected file, which `clean` reads to undo it. Keep the sidecar with the
protected file if you want to be able to clean it. No single vector reaches every
extractor (a text box and tracked-delete are read by Tika/markitdown but not
python-docx; a header by some pipelines and not others), which is why `--all`
plants the instruction in all of the default (non-research-only) vectors at once.
(`--random` is a deprecated alias for `--all`, kept for backward compatibility;
it never chose vectors randomly — it always applied the full default set.)

**PPTX** ships its own **ten** vectors in the same two families. Flagship is
`speaker_notes` (payload in a slide's speaker notes — invisible in slideshow, read
by every extractor, and a completely normal part of a deck). Structural: `white_text`,
`tiny_font`, `off_slide` (off-canvas text box), `zero_size`, `alt_text`,
`hidden_slide` (a full slide marked `show="0"`). Text-value (sidecar): `speaker_notes`
and `core_props`. The same two in-text encoding vectors (`unicode_tags`, `zero_width`)
are carried over as research-only. The PPTX default vector is `speaker_notes`.

**XLSX** ships **eight** vectors. Flagship is `very_hidden_sheet` (a whole
worksheet marked `veryHidden` — not even in Excel's Unhide menu, yet read by
openpyxl/pandas/markitdown). Also: `semicolon_format` (the `;;;` number format:
value present, displays blank — text-value/sidecar), `white_fill` (white-on-white),
`hidden_row`, `hidden_col`, `header_footer` (printed-only page header), `comment`
(cell note), and `core_props` (text-value/sidecar). The payload cells sit far
off-canvas (column AZ, rows 1000+) so they never collide with real data. XLSX has
**no** in-text encoding vectors: openpyxl strips the Unicode Tags / zero-width
codepoints on save, and the experiment showed no model decodes them anyway — an
honest, documented format difference from DOCX/PPTX. XLSX is sidecar-only for
reversal (openpyxl reserializes the whole workbook, so an inline marker would not
survive), so keep the `*.scarecrow.json` sidecar with the protected file to clean it.

## Limitations (read this)

This is a **deterrent against careless ingestion, not a lock.** It targets a
naive-to-moderate attacker who does not know Scarecrow exists and does not
pre-process the file. A determined adversary who knows the trick can strip the
hidden text out, or screenshot the page and read the pixels (OCR), and defeat it.
Frontier models are also a moving target. Treat it like a "keep out" sign, not a
safe. For anything genuinely sensitive, use real access controls.

## Features at a glance

- **Three formats** — DOCX, PPTX, XLSX, each with its own vector library.
- **Three payload modes** — `refuse`, `corrupt`, and `canary` (beacon / breach
  detection via a caller-supplied URL).
- **One CLI** — `protect` / `clean` / `inspect` / `list-vectors`, with `--json`
  output and `--vectors` / `--all` / `--in-place` control.
- **Fully reversible** — `clean` removes every injected element and restores
  metadata, returning the document to structural equivalence.
- **Python 3.11+**, installable via `pipx install .` or `pip install -e .`.

## Development

```
pip install -e ".[dev]"
pytest                # the full Layer-1 test suite (runs in CI)
```
