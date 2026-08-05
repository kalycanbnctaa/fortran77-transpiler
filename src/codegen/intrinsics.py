from __future__ import annotations

UNARY_MATH_FUNCTIONS = {
    "SQRT": "sqrtf",
    "EXP": "expf",
    "LOG": "logf",
    "LOG10": "log10f",
    "SIN": "sinf",
    "COS": "cosf",
    "TAN": "tanf",
}


class IntrinsicCodegenError(Exception):
    pass


def emit_intrinsic(name: str, arg_texts: list[str], arg_types: list[str]) -> str:
    if name == "MAX":
        return _reduce_ternary(arg_texts, ">")
    if name == "MIN":
        return _reduce_ternary(arg_texts, "<")
    if name == "ABS":
        return f"fabsf({arg_texts[0]})" if arg_types[0] == "REAL" else f"abs({arg_texts[0]})"
    if name == "IABS":
        return f"abs({arg_texts[0]})"
    if name == "MOD":
        if "REAL" in arg_types:
            return f"fmodf({arg_texts[0]}, {arg_texts[1]})"
        return f"({arg_texts[0]} % {arg_texts[1]})"
    if name == "INT":
        return f"(int)({arg_texts[0]})"
    if name == "REAL":
        return f"(float)({arg_texts[0]})"
    if name in UNARY_MATH_FUNCTIONS:
        return f"{UNARY_MATH_FUNCTIONS[name]}({arg_texts[0]})"
    raise IntrinsicCodegenError(f"Unknown intrinsic '{name}'")


def _reduce_ternary(args: list[str], operator: str) -> str:
    expr = args[0]
    for arg in args[1:]:
        expr = f"(({expr}){operator}({arg})?({expr}):({arg}))"
    return expr