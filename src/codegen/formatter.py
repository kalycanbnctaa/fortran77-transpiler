from __future__ import annotations

C_TYPE_MAP: dict[str, str] = {
    "INTEGER": "int",
    "REAL": "float",
    "LOGICAL": "int",
    "CHARACTER": "char",
}

FORMAT_SPECIFIER_MAP: dict[str, str] = {
    "INTEGER": "%d",
    "REAL": "%f",
    "LOGICAL": "%d",
    "CHARACTER": "%s",
}

SCAN_SPECIFIER_MAP: dict[str, str] = {
    "INTEGER": "%d",
    "REAL": "%f",
    "LOGICAL": "%d",
    "CHARACTER": "%s",
}

def c_type(base_type: str) -> str:
    if base_type not in C_TYPE_MAP:
        raise ValueError(f"Unsupported Fortran type '{base_type}'")
    return C_TYPE_MAP[base_type]

def format_specifier(base_type: str) -> str:
    if base_type not in FORMAT_SPECIFIER_MAP:
        raise ValueError(f"Unsupported Fortran type '{base_type}'")
    return FORMAT_SPECIFIER_MAP[base_type]

def scan_specifier(base_type: str) -> str:
    if base_type not in SCAN_SPECIFIER_MAP:
        raise ValueError(f"Unsupported Fortran type '{base_type}'")
    return SCAN_SPECIFIER_MAP[base_type]

def c_identifier(name: str) -> str:
    return name.lower()

def format_int_literal(value: int) -> str:
    return str(value)

def format_real_literal(value: float) -> str:
    text = repr(float(value))
    if "e" in text or "E" in text:
        return text
    if "." not in text:
        text = f"{text}.0"
    return text

def format_logical_literal(value: bool) -> str:
    return "1" if value else "0"

def format_character_literal(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'

def character_buffer_size(length: int | None) -> int:
    return (length if length is not None else 1) + 1