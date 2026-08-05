from __future__ import annotations

from pathlib import Path

import pytest

from tests.helpers import generate_and_run_c, run_fortran

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"

EXAMPLE_FILES = [
    "hello.f",
    "basic/fixed_form_demo.f",
    "basic/lexer_demo.f",
    "basic/scalar_ops.f",
    "common/sumsquares.f",
    "arrays/matsum.f",
]

def _tokens_match(expected_token: str, actual_token: str) -> bool:
    try:
        ef = float(expected_token)
        af = float(actual_token)
        return abs(ef - af) <= 1e-4
    except ValueError:
        return expected_token == actual_token

def outputs_match(expected: str, actual: str) -> bool:
    exp_lines = expected.splitlines()
    act_lines = actual.splitlines()
    if len(exp_lines) != len(act_lines):
        return False
    for exp_line, act_line in zip(exp_lines, act_lines):
        exp_tokens = exp_line.split()
        act_tokens = act_line.split()
        if len(exp_tokens) != len(act_tokens):
            return False
        for exp_token, act_token in zip(exp_tokens, act_tokens):
            if not _tokens_match(exp_token, act_token):
                return False
    return True

@pytest.mark.parametrize("rel_path", EXAMPLE_FILES)
def test_example(rel_path: str) -> None:
    fortran_path = EXAMPLES_DIR / rel_path
    if not fortran_path.exists():
        pytest.skip(f"File {fortran_path} not found")

    expected = run_fortran(fortran_path)
    actual = generate_and_run_c(fortran_path)

    assert outputs_match(expected, actual), f"Output mismatch for {rel_path}"