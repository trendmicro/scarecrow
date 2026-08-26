"""Scarecrow CLI.

Implements ``protect`` / ``clean`` / ``inspect`` / ``list-vectors`` for DOCX and
PPTX, each with its own vector library and all three payload modes (``refuse`` /
``corrupt`` / ``canary``). The format is chosen by file extension. Not-yet-built
surface (XLSX) fails with a clear message rather than pretending to work.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from scarecrow.core.marker import Marker, write_sidecar
from scarecrow.core.modes import Mode
from scarecrow.core.payloads import reinforce_payload, select_payload

app = typer.Typer(
    help="Insert prompt injections into Office files so humans read them "
    "normally but an ingesting LLM is derailed.",
    no_args_is_help=True,
    add_completion=False,
)

# Importing a format package registers its vectors. DOCX + PPTX + XLSX supported.
from scarecrow.formats import docx as _docx  # noqa: E402,F401
from scarecrow.formats import pptx as _pptx  # noqa: E402,F401
from scarecrow.formats import xlsx as _xlsx  # noqa: E402,F401
from scarecrow import vector  # noqa: E402

# Supported formats -> the file extension.
_SUPPORTED = {".docx": "docx", ".pptx": "pptx", ".xlsx": "xlsx"}


@app.callback()
def _main() -> None:
    """Scarecrow. Subcommands: protect, clean, inspect, list-vectors."""


def _default_output(src: Path) -> Path:
    """foo.docx -> foo.scarecrow.docx (default: write a new file)."""
    return src.with_suffix(f".scarecrow{src.suffix}")


def _format_of(file: Path) -> str:
    """Return the Scarecrow format key for `file`, or reject unsupported extensions."""
    fmt = _SUPPORTED.get(file.suffix.lower())
    if fmt is None:
        raise typer.BadParameter(
            f"unsupported format {file.suffix!r}; supported: "
            f"{', '.join(sorted(_SUPPORTED))}")
    return fmt


def _load(file: Path, fmt: str):
    """Open `file` with the right library for its format."""
    if fmt == "docx":
        from docx import Document
        return Document(str(file))
    if fmt == "pptx":
        from pptx import Presentation
        return Presentation(str(file))
    from openpyxl import load_workbook
    return load_workbook(str(file))


def _clean_fn(fmt: str):
    """The clean_<fmt>(in, out) -> count function for this format."""
    if fmt == "docx":
        from scarecrow.formats.docx.reverse import clean_docx
        return clean_docx
    if fmt == "pptx":
        from scarecrow.formats.pptx.reverse import clean_pptx
        return clean_pptx
    from scarecrow.formats.xlsx.reverse import clean_xlsx
    return clean_xlsx


def _inspect_fn(fmt: str):
    """The inspect_<fmt>(path) -> list[Injection] function for this format."""
    if fmt == "docx":
        from scarecrow.formats.docx.reverse import inspect_docx
        return inspect_docx
    if fmt == "pptx":
        from scarecrow.formats.pptx.reverse import inspect_pptx
        return inspect_pptx
    from scarecrow.formats.xlsx.reverse import inspect_xlsx
    return inspect_xlsx


# Per-format default vector when neither --vectors nor --all is given.
_DEFAULT_VECTOR = {"docx": "vanish", "pptx": "speaker_notes", "xlsx": "very_hidden_sheet"}

# Per-format second vector used to carry the reinforcement (scope-closing) payload when
# reinforced protection is on (the default for REFUSE mode). A distinct structural hiding
# place from the flagship so the two payloads do not collide, and one every whole-file
# extractor surfaces. Benchmarks: plain + scope-closing = 12/14 vs 11/14 plain.
_REINFORCE_VECTOR = {"docx": "header_footer", "pptx": "off_slide", "xlsx": "comment"}


def _resolve_vectors(vectors: str | None, use_all: bool, fmt: str) -> list:
    """Pick which vectors to apply for `fmt`: --vectors names, --all, or the default."""
    if vectors and use_all:
        raise typer.BadParameter("--vectors and --all are mutually exclusive")
    if use_all:
        return vector.default_vectors(fmt)  # every vector minus the research-only ones
    if vectors:
        chosen = []
        known_here = {v.name for v in vector.all_vectors(fmt)}
        for name in [n.strip() for n in vectors.split(",") if n.strip()]:
            if name not in known_here:
                avail = ", ".join(v.name for v in vector.all_vectors(fmt))
                raise typer.BadParameter(
                    f"unknown {fmt} vector {name!r}; available: {avail}")
            chosen.append(vector.get(name, fmt))
        return chosen
    return [vector.get(_DEFAULT_VECTOR[fmt], fmt)]  # the format's flagship


@app.command("protect")
def protect(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True,
                                help="the .docx to protect"),
    mode: Mode = typer.Option(Mode.REFUSE, "--mode", help="payload behaviour"),
    vectors: str | None = typer.Option(
        None, "--vectors", help="comma-separated vector names (default: the format's flagship)"),
    use_all: bool = typer.Option(
        False, "--all", "--random",
        help="apply the whole default vector set (all vectors except the "
        "research-only in-text encodings; select those explicitly with --vectors). "
        "--random is a deprecated alias."),
    payload_file: Path | None = typer.Option(
        None, "--payload-file", exists=True, dir_okay=False,
        help="override the built-in payload"),
    no_reinforce: bool = typer.Option(
        False, "--no-reinforce",
        help="plant only one payload. By default (REFUSE mode, built-in payload) protect "
        "also plants a complementary scope-closing payload in a second vector, which "
        "benchmarks show protects one more model (12/14 vs 11/14) with none lost. This "
        "flag disables that and reverts to a single payload."),
    canary_url: str | None = typer.Option(
        None, "--canary-url", help="beacon URL (required for --mode canary)"),
    output: Path | None = typer.Option(
        None, "--output", help="output path (default: <name>.scarecrow.<ext>)"),
    in_place: bool = typer.Option(
        False, "--in-place", help="overwrite the input file (opt-in)"),
) -> None:
    """Protect a document by embedding a hidden derail payload."""
    fmt = _format_of(file)

    if in_place and output is not None:
        raise typer.BadParameter("--in-place and --output are mutually exclusive")
    out_path = file if in_place else (output or _default_output(file))

    # Validate the mode / canary-url combination before touching the file.
    if mode is Mode.CANARY and not canary_url:
        raise typer.BadParameter("--mode canary requires --canary-url URL")
    if mode is not Mode.CANARY and canary_url:
        raise typer.BadParameter(
            f"--canary-url only applies to --mode canary, not {mode.value!r}")

    chosen = _resolve_vectors(vectors, use_all, fmt)

    payload = select_payload(
        mode, str(payload_file) if payload_file else None, canary_url)

    # Reinforced protection: plant a complementary scope-closing payload in a second
    # vector. On by default for the built-in REFUSE payload (benchmarks: 12/14 vs 11/14).
    # Not applied when the user overrides the payload (--payload-file), disables it
    # (--no-reinforce), or the format's reinforce vector is already one of the chosen
    # (which would double-use it) or unavailable.
    reinforce_text = None if (payload_file or no_reinforce) else reinforce_payload(mode)
    reinforce_vec = None
    if reinforce_text is not None:
        rv_name = _REINFORCE_VECTOR.get(fmt)
        chosen_names = {v.name for v in chosen}
        if rv_name and rv_name not in chosen_names:
            reinforce_vec = vector.get(rv_name, fmt)

    # Apply every chosen vector with the main payload, then the reinforcement vector with
    # the scope-closing payload, all under one marker so clean() removes them together.
    doc = _load(file, fmt)
    marker = Marker()
    for v in chosen:
        v.apply(doc, payload, marker)
    if reinforce_vec is not None:
        reinforce_vec.apply(doc, reinforce_text, marker)
    doc.save(str(out_path))

    # Write the sidecar if any text-value vector recorded an entry.
    sidecar = write_sidecar(str(out_path), marker.sidecar_entries)

    typer.echo(f"Protected: {out_path}")
    typer.echo(f"  mode:    {mode.value}")
    if mode is Mode.CANARY:
        typer.echo(f"  canary:  {canary_url}")
    applied = [v.name for v in chosen]
    if reinforce_vec is not None:
        applied.append(f"{reinforce_vec.name} (reinforce)")
    typer.echo(f"  vectors: {', '.join(applied)}")
    typer.echo(f"  marker:  {marker.run_id}")
    if sidecar is not None:
        typer.echo(f"  sidecar: {sidecar}")


@app.command("clean")
def clean(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True,
                                help="the protected .docx to clean"),
    output: Path | None = typer.Option(
        None, "--output", help="output path (default: <name>.cleaned.<ext>)"),
    in_place: bool = typer.Option(
        False, "--in-place", help="overwrite the input file (opt-in)"),
) -> None:
    """Remove Scarecrow's injected content, restoring the original document."""
    fmt = _format_of(file)
    if in_place and output is not None:
        raise typer.BadParameter("--in-place and --output are mutually exclusive")
    out_path = file if in_place else (output or file.with_suffix(f".cleaned{file.suffix}"))

    removed = _clean_fn(fmt)(str(file), str(out_path))

    if removed == 0:
        typer.echo(f"No Scarecrow injections found in {file}; wrote an unchanged copy to {out_path}")
    else:
        typer.echo(f"Cleaned: {out_path}")
        typer.echo(f"  removed {removed} injection(s)")


@app.command("inspect")
def inspect(
    file: Path = typer.Argument(..., exists=True, dir_okay=False, readable=True,
                                help="the .docx to inspect"),
    as_json: bool = typer.Option(False, "--json", help="emit JSON instead of text"),
) -> None:
    """Report what Scarecrow has injected into a document."""
    fmt = _format_of(file)
    injections = _inspect_fn(fmt)(str(file))

    if as_json:
        typer.echo(json.dumps(
            [{"vector": i.vector, "run_id": i.run_id, "where": i.where, "text": i.text}
             for i in injections], ensure_ascii=False, indent=2))
        return

    if not injections:
        typer.echo(f"{file}: no Scarecrow injections found.")
        return
    typer.echo(f"{file}: {len(injections)} injection(s) found")
    for i in injections:
        preview = (i.text[:64] + "…") if len(i.text) > 64 else i.text
        typer.echo(f"  [{i.vector}] run {i.run_id} ({i.where}): {preview!r}")


@app.command("list-vectors")
def list_vectors(
    fmt: str | None = typer.Option(None, "--format", help="filter by format (docx/xlsx/pptx)"),
    as_json: bool = typer.Option(False, "--json", help="emit JSON instead of text"),
) -> None:
    """List the available injection vectors."""
    vs = vector.all_vectors(fmt)  # type: ignore[arg-type]
    if as_json:
        typer.echo(json.dumps(
            [{"name": v.name, "format": v.format, "marker_kind": v.marker_kind,
              "description": getattr(v, "description", ""),
              "default_random": vector.default_random(v)} for v in vs],
            ensure_ascii=False, indent=2))
        return
    if not vs:
        typer.echo("No vectors registered" + (f" for format {fmt!r}." if fmt else "."))
        return
    for v in vs:
        flag = "" if vector.default_random(v) else "  (research-only, not in --all)"
        typer.echo(f"  {v.name:14} [{v.format}/{v.marker_kind}]  {getattr(v, 'description', '')}{flag}")


if __name__ == "__main__":
    app()
