from __future__ import annotations

from pathlib import Path


class SourceScanner:
    def __init__(self, source: str) -> None:
        self._source = source

    @classmethod
    def from_file(cls, path: Path) -> "SourceScanner":
        source = path.read_text(encoding="utf-8")
        return cls(source)

    @classmethod
    def from_text(cls, text: str) -> "SourceScanner":
        return cls(text)

    def read(self) -> str:
        return self._source

    def read_lines(self) -> list[str]:
        return self._source.splitlines()