from __future__ import annotations


class Emitter:
    def __init__(self, indent_size: int = 4) -> None:
        self._lines: list[str] = []
        self._indent_size = indent_size
        self._level = 0

    def indent(self) -> None:
        self._level += 1

    def dedent(self) -> None:
        self._level = max(0, self._level - 1)

    def line(self, text: str = "") -> None:
        if text:
            self._lines.append(" " * (self._indent_size * self._level) + text)
        else:
            self._lines.append("")

    def blank(self) -> None:
        self._lines.append("")

    def render(self) -> str:
        source = "\n".join(self._lines)
        return source.rstrip("\n") + "\n"