from __future__ import annotations

from src.codegen.emitter import Emitter


def test_line_without_text_is_blank():
    emitter = Emitter()
    emitter.line()
    assert emitter.render() == "\n"


def test_line_with_text_at_base_indent():
    emitter = Emitter()
    emitter.line("int main(void) {")
    assert emitter.render() == "int main(void) {\n"


def test_indent_prefixes_four_spaces_by_default():
    emitter = Emitter()
    emitter.line("int main(void) {")
    emitter.indent()
    emitter.line("return 0;")
    emitter.dedent()
    emitter.line("}")
    assert emitter.render() == "int main(void) {\n    return 0;\n}\n"


def test_dedent_never_goes_below_zero():
    emitter = Emitter()
    emitter.dedent()
    emitter.line("x")
    assert emitter.render() == "x\n"


def test_blank_adds_empty_line():
    emitter = Emitter()
    emitter.line("a")
    emitter.blank()
    emitter.line("b")
    assert emitter.render() == "a\n\nb\n"


def test_render_ends_with_single_trailing_newline():
    emitter = Emitter()
    emitter.line("a")
    emitter.blank()
    emitter.blank()
    rendered = emitter.render()
    assert rendered.endswith("\n")
    assert not rendered.endswith("\n\n")