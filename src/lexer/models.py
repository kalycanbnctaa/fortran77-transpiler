from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class NormalizedLine:
    source_line: int
    raw: str
    label: int | None
    statement: str