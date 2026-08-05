from __future__ import annotations

import tempfile
from pathlib import Path

from tests.helpers import generate_and_run_c, run_fortran

FORTRAN_SOURCE = """\
      PROGRAM CHAR
      IMPLICIT NONE
      CHARACTER S1, S2
      S1 = 'Hello'
      S2 = 'World'
      PRINT *, S1
      PRINT *, S2
      IF (S1 .EQ. S2) THEN
          PRINT *, 'Same'
      ELSE
          PRINT *, 'Different'
      ENDIF
      END
"""

def test_character() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".f", delete=False) as f:
        f.write(FORTRAN_SOURCE)
        fortran_path = Path(f.name)

    try:
        expected = run_fortran(fortran_path)
        actual = generate_and_run_c(fortran_path)
        assert actual == expected
    finally:
        fortran_path.unlink(missing_ok=True)