"""PPTX speaker-notes vector (text-value / sidecar) — the flagship PPTX technique.

The payload goes in a slide's speaker notes (`ppt/notesSlides/notesSlideN.xml`).
Notes are invisible during F5 slideshow playback (they show only on the presenter's
own screen in presenter view), yet every mainstream extractor pulls them out:
python-pptx (`slide.notes_slide`), Tika, markitdown, LibreOffice, unstructured all
read the notes part. This is arguably the single strongest vector in the whole
tool — notes are a completely normal, expected part of a deck, so nothing about a
protected file looks unusual.

Text-value: the payload *is* the notes text, so there is nowhere to put an inline
`sc:` marker without the LLM seeing it. `apply` records a sidecar entry (the slide
index and the previous notes text); `clean` restores it.
"""

from __future__ import annotations

from scarecrow.core.marker import Marker
from scarecrow.vector import register


class SpeakerNotesVector:
    name = "speaker_notes"
    format = "pptx"
    marker_kind = "text-value"
    description = "payload in a slide's speaker notes (flagship; invisible in slideshow)"

    def apply(self, doc: object, payload: str, marker: Marker) -> None:
        # Put the payload in the first slide's notes (deterministic + early in the
        # extracted stream). notes_slide is created on first access.
        slide = doc.slides[0]                     # type: ignore[attr-defined]
        tf = slide.notes_slide.notes_text_frame
        previous = tf.text or ""
        tf.text = payload
        marker.record_sidecar(self.name, "slide:0", payload, previous)

    def clean(self, doc: object, marker: Marker) -> None:
        # text-value: structural clean is a no-op; the reverse driver calls
        # clean_from_sidecar. Kept for protocol conformance.
        return

    def clean_from_sidecar(self, doc: object, entry: dict) -> None:
        """Restore the notes text this vector overwrote, from a sidecar entry."""
        idx = int(entry["location"].split(":")[1])
        slide = doc.slides[idx]                   # type: ignore[attr-defined]
        slide.notes_slide.notes_text_frame.text = entry.get("previous") or ""


register(SpeakerNotesVector())
