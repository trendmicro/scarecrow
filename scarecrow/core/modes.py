"""Payload modes.

A mode is *what the injection tries to make the ingesting LLM do*:

  refuse   — the LLM declines to summarize / answer. Easiest to test, clearest
             pass/fail. Slice 1 target.
  corrupt  — the LLM returns plausible-but-wrong output. (Payloads: Slice 4.)
  canary   — the LLM emits a beacon (echoes a token / requests a URL). Doubles as
             breach detection. Requires --canary-url. (Payloads: Slice 4.)

The enum exists in full from Slice 1 so the CLI surface and payload-selection
logic are stable; only the refuse payloads are populated here. corrupt/canary
raise a clear NotImplementedError until Slice 4 rather than silently shipping a
weak payload.
"""

from __future__ import annotations

from enum import Enum


class Mode(str, Enum):
    REFUSE = "refuse"
    CORRUPT = "corrupt"
    CANARY = "canary"
