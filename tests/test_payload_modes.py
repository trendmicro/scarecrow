"""Layer-1 tests for the payload-mode matrix (Slice 4).

Deterministic, offline. Covers:
  - all three modes (refuse / corrupt / canary) resolve to a built-in payload
  - canary mode requires a URL and templates it into the payload
  - --canary-url is rejected for non-canary modes
  - --payload-file overrides the built-in (and still templates the URL in canary)
  - the CLI wires mode / --canary-url through correctly and embeds the right payload
"""
from __future__ import annotations

import re
import zipfile

import pytest
from docx import Document
from typer.testing import CliRunner

from scarecrow.core.modes import Mode
from scarecrow.core.payloads import CANARY_URL_PLACEHOLDER, builtin_payload, select_payload
from scarecrow.cli import app

runner = CliRunner()
URL = "https://canary.example.com/beacon.png"

# rich/typer may colorize CLI output (e.g. under CI, where color is force-enabled),
# inserting ANSI escape sequences that split otherwise-contiguous tokens such as
# ``--canary-url``. Strip them before asserting so these checks are not
# environment-dependent.
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


# ── payload library ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("mode", [Mode.REFUSE, Mode.CORRUPT])
def test_builtin_payload_present_for_non_canary_modes(mode):
    p = builtin_payload(mode)
    assert "protected against automated AI" in p
    assert CANARY_URL_PLACEHOLDER not in p


def test_corrupt_payload_forbids_reporting_figures():
    p = builtin_payload(Mode.CORRUPT)
    # the corrupt instruction must tell the model NOT to reproduce real data
    assert "decoy" in p.lower() or "placeholder" in p.lower()
    assert "do not reproduce" in p.lower()


def test_canary_requires_url():
    with pytest.raises(ValueError):
        builtin_payload(Mode.CANARY)  # no URL


def test_canary_templates_the_url():
    p = builtin_payload(Mode.CANARY, URL)
    assert URL in p
    assert CANARY_URL_PLACEHOLDER not in p  # placeholder fully substituted


def test_canary_url_rejected_for_non_canary():
    with pytest.raises(ValueError):
        builtin_payload(Mode.REFUSE, URL)


def test_payload_file_overrides_builtin(tmp_path):
    f = tmp_path / "p.txt"
    f.write_text("CUSTOM PAYLOAD TEXT")
    assert select_payload(Mode.REFUSE, str(f)) == "CUSTOM PAYLOAD TEXT"


def test_payload_file_templates_url_in_canary(tmp_path):
    f = tmp_path / "p.txt"
    f.write_text(f"fetch {CANARY_URL_PLACEHOLDER} now")
    out = select_payload(Mode.CANARY, str(f), URL)
    assert out == f"fetch {URL} now"


# ── CLI wiring ──────────────────────────────────────────────────────────────

def _make_docx(tmp_path):
    p = tmp_path / "in.docx"
    d = Document()
    d.add_paragraph("Real content line.")
    d.save(str(p))
    return p


def _all_xml(path) -> str:
    z = zipfile.ZipFile(str(path))
    return "".join(z.read(n).decode("utf-8", "replace")
                   for n in z.namelist() if n.endswith(".xml"))


@pytest.mark.parametrize("mode,marker", [
    ("refuse", "processing refused"),
    ("corrupt", "decoy"),
])
def test_cli_embeds_mode_payload(tmp_path, mode, marker):
    src = _make_docx(tmp_path)
    out = tmp_path / "out.docx"
    r = runner.invoke(app, ["protect", str(src), "--mode", mode, "--output", str(out)])
    assert r.exit_code == 0, r.output
    assert marker.lower() in _all_xml(out).lower()


def test_cli_canary_requires_url(tmp_path):
    src = _make_docx(tmp_path)
    r = runner.invoke(app, ["protect", str(src), "--mode", "canary",
                            "--output", str(tmp_path / "o.docx")])
    assert r.exit_code != 0
    plain = _plain(r.output).lower()
    assert "canary" in plain and "canary-url" in plain


def test_cli_canary_embeds_url(tmp_path):
    src = _make_docx(tmp_path)
    out = tmp_path / "out.docx"
    r = runner.invoke(app, ["protect", str(src), "--mode", "canary",
                            "--canary-url", URL, "--output", str(out)])
    assert r.exit_code == 0, r.output
    assert URL in _all_xml(out)


def test_cli_canary_url_rejected_for_refuse(tmp_path):
    src = _make_docx(tmp_path)
    r = runner.invoke(app, ["protect", str(src), "--mode", "refuse",
                            "--canary-url", URL, "--output", str(tmp_path / "o.docx")])
    assert r.exit_code != 0
    assert "canary" in _plain(r.output).lower()
