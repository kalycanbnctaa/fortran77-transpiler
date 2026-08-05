from __future__ import annotations

import tempfile
from pathlib import Path

from tests.helpers import generate_and_run_c, run_fortran

FORTRAN_SOURCE = """\
      PROGRAM COMPGOTO
      IMPLICIT NONE
      INTEGER I
      I = 2
      GOTO (10,20,30), I
   10 PRINT *, 'Label 10'
      GOTO 99
   20 PRINT *, 'Label 20'
      GOTO 99
   30 PRINT *, 'Label 30'
   99 CONTINUE
      END
"""

def test_computed_goto() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".f", delete=False) as f:
        f.write(FORTRAN_SOURCE)
        fortran_path = Path(f.name)

    try:
        expected = run_fortran(fortran_path)
        actual = generate_and_run_c(fortran_path)
        assert actual == expected
    finally:
        fortran_path.unlink(missing_ok=True)