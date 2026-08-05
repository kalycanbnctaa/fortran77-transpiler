from __future__ import annotations

from .models import NormalizedLine

COMMENT_MARKERS = ("C", "c", "*")
LABEL_START = 0
LABEL_END = 5
CONTINUATION_COL = 5
STATEMENT_START = 6
STATEMENT_END = 72

class FixedFormProcessor:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def normalize(self) -> list[NormalizedLine]:
        normalized: list[NormalizedLine] = []

        for line_number, raw_line in enumerate(self._lines, start=1):
            if self._is_blank(raw_line):
                continue

            if self._is_comment(raw_line):
                continue

            padded = raw_line.ljust(STATEMENT_END)
            label_field = padded[LABEL_START:LABEL_END].strip()
            is_continuation = self._is_continuation(padded) and not label_field
            statement = padded[STATEMENT_START:STATEMENT_END].strip()

            if is_continuation:
                if not normalized:
                    raise ValueError(
                        f"Line {line_number}: continuation marker found "
                        "but there is no previous statement to continue."
                    )
                previous = normalized[-1]
                previous.statement = f"{previous.statement} {statement}".strip()
                continue

            label = self._extract_label(padded, line_number)

            normalized.append(
                NormalizedLine(
                    source_line=line_number,
                    raw=raw_line,
                    label=label,
                    statement=statement,
                )
            )

        return normalized

    @staticmethod
    def _is_blank(line: str) -> bool:
        return line.strip() == ""

    @staticmethod
    def _is_comment(line: str) -> bool:
        return line[0:1] in COMMENT_MARKERS

    @staticmethod
    def _extract_label(padded_line: str, line_number: int) -> int | None:
        label_field = padded_line[LABEL_START:LABEL_END].strip()
        if not label_field:
            return None
        if not label_field.isdigit():
            raise ValueError(
                f"Line {line_number}: columns 1-5 must contain only a "
                f"numeric label or be blank, got {label_field!r}."
            )
        return int(label_field)

    @staticmethod
    def _is_continuation(padded_line: str) -> bool:
        marker = padded_line[CONTINUATION_COL]
        return marker not in (" ", "0")