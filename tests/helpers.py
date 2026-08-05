from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

from main import generate_code

def normalize_output(text: str) -> str:
    """Hilangkan spasi berlebih, biarkan angka float apa adanya."""
    return "\n".join(line.strip() for line in text.strip().splitlines())

def compile_fortran(source: Path, output: Path) -> None:
    subprocess.run(
        ["gfortran", str(source), "-o", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

def compile_c(source: Path, output: Path) -> None:
    subprocess.run(
        ["gcc", str(source), "-o", str(output), "-lm"],
        check=True,
        capture_output=True,
        text=True,
    )

def run_executable(exe: Path) -> str:
    result = subprocess.run(
        [str(exe)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout

def run_fortran(source: Path) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        exe = Path(tmpdir) / "a.out"
        compile_fortran(source, exe)
        return normalize_output(run_executable(exe))

def run_c(source: Path) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        exe = Path(tmpdir) / "a.out"
        compile_c(source, exe)
        return normalize_output(run_executable(exe))

def transpile(input_path: Path, source_map: bool = False) -> str:
    return generate_code(input_path, source_map)

def generate_and_run_c(input_path: Path, source_map: bool = False) -> str:
    code = transpile(input_path, source_map)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        f.write(code)
        c_path = Path(f.name)
    try:
        return run_c(c_path)
    finally:
        c_path.unlink(missing_ok=True)