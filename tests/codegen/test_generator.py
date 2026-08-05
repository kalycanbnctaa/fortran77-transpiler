from __future__ import annotations

import pytest

from src.codegen.generator import CodeGenerationError
from src.semantic.scope import SemanticError

from .helpers import generate, generate_example

def test_headers_are_always_included():
    code = generate(["      PROGRAM T", "      IMPLICIT NONE", "      END"])
    assert "#include <stdio.h>" in code
    assert "#include <math.h>" in code
    assert "#include <stdlib.h>" in code

def test_program_becomes_int_main():
    code = generate(["      PROGRAM T", "      IMPLICIT NONE", "      END"])
    assert "int main(void) {" in code
    assert code.rstrip().endswith("}")

def test_program_always_returns_zero():
    code = generate(["      PROGRAM T", "      IMPLICIT NONE", "      END"])
    assert "return 0;" in code

def test_hello_example_generates_expected_print():
    code = generate_example("examples/hello.f")
    assert 'printf("%d\\n", 123);' in code

def test_scalar_ops_example_generates_declarations_and_statements():
    code = generate_example("examples/basic/scalar_ops.f")
    assert "int n, i;" in code
    assert "float x, y, result;" in code
    assert "n = 5;" in code
    assert "x = 3.5;" in code
    assert "y = 2.0;" in code
    assert "result = ((x * y) + (n / 2.0));" in code
    assert 'printf("%d\\n", n);' in code
    assert 'printf("%f\\n", result);' in code

def test_read_generates_scanf_with_address_of():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      READ *, N",
            "      END",
        ]
    )
    assert 'scanf("%d", &(n));' in code

def test_read_multiple_targets():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      REAL X",
            "      READ *, N, X",
            "      END",
        ]
    )
    assert 'scanf("%d %f", &(n), &(x));' in code

def test_print_with_no_items_still_emits_newline():
    code = generate(["      PROGRAM T", "      IMPLICIT NONE", "      PRINT *", "      END"])
    assert 'printf("\\n");' in code

def test_arithmetic_expression_uses_c_operators():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER A, B, C",
            "      C = A + B - 1",
            "      END",
        ]
    )
    assert "c = ((a + b) - 1);" in code

def test_power_operator_integer_operands_uses_llround():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER X, Y",
            "      Y = X ** 2",
            "      END",
        ]
    )
    assert "y = (int)llround(pow(x, 2));" in code

def test_power_operator_real_operand_uses_plain_pow():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      REAL X, Y",
            "      Y = X ** 2",
            "      END",
        ]
    )
    assert "y = pow(x, 2);" in code

def test_unary_minus():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER X, Y",
            "      Y = -X",
            "      END",
        ]
    )
    assert "y = -x;" in code

def test_array_declaration_and_assignment():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER A(3,2)",
            "      A(1,1) = 1",
            "      A(2,1) = 2",
            "      END",
        ]
    )
    assert "int a[6];" in code
    assert "a[(1-1) + (1-1)*3] = 1;" in code
    assert "a[(2-1) + (1-1)*3] = 2;" in code

def test_matsum_example_matches_spec_offsets():
    code = generate_example("examples/arrays/matsum.f")
    assert "int a[6];" in code
    assert "int i, j, total;" in code
    assert "a[(1-1) + (1-1)*3] = 1;" in code
    assert "a[(2-1) + (1-1)*3] = 2;" in code
    assert "a[(1-1) + (2-1)*3] = 4;" in code
    assert "for (i = 1; i <= 3; i++) {" in code
    assert "for (j = 1; j <= 2; j++) {" in code
    assert "total = (total + a[(i-1) + (j-1)*3]);" in code
    assert 'printf("%d\\n", total);' in code

def test_if_then_else():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      REAL X",
            "      IF (N .GT. 0) THEN",
            "          X = 1.0",
            "      ELSE",
            "          X = 0.0",
            "      ENDIF",
            "      END",
        ]
    )
    assert "if ((n > 0)) {" in code
    assert "x = 1.0;" in code
    assert "} else {" in code
    assert "x = 0.0;" in code

def test_do_loop_basic():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER I, TOTAL",
            "      TOTAL = 0",
            "      DO 10 I = 1, 5",
            "          TOTAL = TOTAL + I",
            "   10 CONTINUE",
            "      END",
        ]
    )
    assert "for (i = 1; i <= 5; i++) {" in code
    assert "total = (total + i);" in code
    assert "L10: ;" in code

def test_do_loop_with_step():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER I, N",
            "      N = 10",
            "      DO 10 I = 1, N, 3",
            "   10 CONTINUE",
            "      END",
        ]
    )
    assert "for (i = 1; i <= n; i += 3) {" in code

def test_do_loop_with_negative_constant_step_uses_ge():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER I",
            "      DO 10 I = 10, 1, -1",
            "   10 CONTINUE",
            "      END",
        ]
    )
    assert "for (i = 10; i >= 1; i += -1) {" in code

def test_do_loop_with_variable_step_uses_dynamic_condition():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER I, N, S",
            "      N = 1",
            "      S = -1",
            "      DO 10 I = 10, N, S",
            "   10 CONTINUE",
            "      END",
        ]
    )
    assert "((s) >= 0 ? (i <= n) : (i >= n))" in code

def test_goto_generates_c_goto():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      GOTO 10",
            "   10 CONTINUE",
            "      END",
        ]
    )
    assert "goto L10;" in code
    assert "L10: ;" in code

def test_common_block_generates_struct_and_global_instance():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER X, Y",
            "      COMMON /BLK/ X, Y",
            "      X = 1",
            "      Y = 2",
            "      END",
        ]
    )
    assert "struct blk_t {" in code
    assert "int x;" in code
    assert "int y;" in code
    assert "} blk;" in code
    assert "blk.x = 1;" in code
    assert "blk.y = 2;" in code

def test_subroutine_with_parameter_and_call():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      N = 5",
            "      CALL SHOW(N)",
            "      END",
            "",
            "      SUBROUTINE SHOW(VAL)",
            "      IMPLICIT NONE",
            "      INTEGER VAL",
            "      PRINT *, VAL",
            "      RETURN",
            "      END",
        ]
    )
    assert "void show(int *val);" in code
    assert "show(&n);" in code
    assert "void show(int *val) {" in code
    assert 'printf("%d\\n", (*val));' in code
    assert "return;" in code

def test_subroutine_without_parentheses_supported():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      CALL FOO",
            "      END",
            "",
            "      SUBROUTINE FOO",
            "      IMPLICIT NONE",
            "      END",
        ]
    )
    assert "void foo(void);" in code
    assert "foo();" in code
    assert "void foo(void) {" in code

def test_function_prefix_form_generates_result_variable():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER A, B, X",
            "      A = 3",
            "      B = 4",
            "      X = MULT(A, B)",
            "      END",
            "",
            "      INTEGER FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    assert "int mult(int *a, int *b);" in code
    assert "x = mult(&a, &b);" in code
    assert "int mult(int *a, int *b) {" in code
    assert "int mult_val;" in code
    assert "mult_val = ((*a) * (*b));" in code
    assert "return mult_val;" in code

def test_function_body_declared_form():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER X",
            "      X = MULT(2, 3)",
            "      END",
            "",
            "      FUNCTION MULT(A, B)",
            "      IMPLICIT NONE",
            "      INTEGER MULT, A, B",
            "      MULT = A * B",
            "      END",
        ]
    )
    assert "int _tmp0 = 2;" in code or "int _tmp" in code
    assert "int mult_val;" in code
    assert "mult_val = ((*a) * (*b));" in code
    assert "return mult_val;" in code
    assert "mult(&_tmp" in code

def test_adjustable_array_parameter_offset_uses_dereferenced_bound():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER A(3,2), N, M",
            "      N = 3",
            "      M = 2",
            "      CALL FILL(A, N, M)",
            "      END",
            "",
            "      SUBROUTINE FILL(A, N, M)",
            "      IMPLICIT NONE",
            "      INTEGER N, M",
            "      INTEGER A(N, M)",
            "      INTEGER I, J",
            "      DO 10 I = 1, N",
            "          DO 10 J = 1, M",
            "              A(I,J) = 0",
            "   10 CONTINUE",
            "      END",
        ]
    )
    assert "void fill(int *a, int *n, int *m);" in code
    assert "a[(i-1) + (j-1)*(*n)] = 0;" in code

def test_intrinsic_max_call_in_expression():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER A, B, C",
            "      A = 1",
            "      B = 2",
            "      C = MAX(A, B)",
            "      END",
        ]
    )
    assert "c = ((a)>(b)?(a):(b));" in code

def test_intrinsic_sqrt_call_in_expression():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      REAL X, Y",
            "      X = 4.0",
            "      Y = SQRT(X)",
            "      END",
        ]
    )
    assert "y = sqrtf(x);" in code

def test_sumsquares_example_full_structure():
    code = generate_example("examples/common/sumsquares.f")
    assert "struct acc_t {" in code
    assert "int runtotal;" in code
    assert "int callcnt;" in code
    assert "} acc;" in code
    assert "void addsquare(int *val);" in code
    assert "int main(void) {" in code
    assert "int n, i;" in code
    assert "acc.runtotal = 0;" in code
    assert "acc.callcnt = 0;" in code
    assert "n = 5;" in code
    assert "for (i = 1; i <= n; i++) {" in code
    assert "addsquare(&i);" in code
    assert 'printf("%d\\n", acc.runtotal);' in code
    assert 'printf("%d\\n", acc.callcnt);' in code
    assert "void addsquare(int *val) {" in code
    assert "acc.runtotal = (acc.runtotal + ((*val) * (*val)));" in code
    assert "acc.callcnt = (acc.callcnt + 1);" in code

def test_stop_generates_exit():
    code = generate(["      PROGRAM T", "      IMPLICIT NONE", "      STOP", "      END"])
    assert "exit(0);" in code

def test_unknown_call_target_raises():
    with pytest.raises(SemanticError):
        generate(
            [
                "      PROGRAM T",
                "      IMPLICIT NONE",
                "      CALL FOO",
                "      END",
            ]
        )

def test_print_logical_uses_T_F_not_1_0():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      LOGICAL FLAG",
            "      FLAG = .TRUE.",
            "      PRINT *, FLAG",
            "      END",
        ]
    )
    assert '(flag ? "T" : "F")' in code
    assert '"%s\\n"' in code

def test_print_mixed_types_including_logical():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      INTEGER N",
            "      LOGICAL FLAG",
            "      N = 5",
            "      FLAG = .FALSE.",
            "      PRINT *, N, FLAG",
            "      END",
        ]
    )
    assert '"%d %s\\n"' in code
    assert '(flag ? "T" : "F")' in code

def test_multiple_character_names_in_one_declaration_compiles_correctly():
    code = generate(
        [
            "      PROGRAM T",
            "      IMPLICIT NONE",
            "      CHARACTER S1, S2",
            "      S1 = 'A'",
            "      S2 = 'B'",
            "      END",
        ]
    )
    assert "char s1[2], s2[2];" in code
    assert "char s1[2], char s2[2];" not in code