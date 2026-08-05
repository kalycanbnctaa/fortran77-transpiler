from __future__ import annotations

import tempfile
from pathlib import Path

from tests.helpers import transpile

FORTRAN_SOURCE = """\
      PROGRAM HELLO
      IMPLICIT NONE
      PRINT *, 123
      END
"""

def test_source_map() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".f", delete=False) as f:
        f.write(FORTRAN_SOURCE)
        fortran_path = Path(f.name)

    try:
        code_without_map = transpile(fortran_path, source_map=False)
        code_with_map = transpile(fortran_path, source_map=True)

        assert "// line" not in code_without_map
        assert "// line" in code_with_map

        lines = code_with_map.splitlines()
        comments = [line for line in lines if "// line" in line]
        assert len(comments) >= 2
    finally:
        fortran_path.unlink(missing_ok=True)