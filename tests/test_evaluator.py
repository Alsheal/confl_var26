"""Tests of the translation: values, constants and expressions."""

import math

import pytest

from confl.converter import translate
from confl.errors import ConfigError, ConfigSemanticError

SQRT_TWO = math.sqrt(2)

VALUE_CASES = [
    ("0", 0),
    ("007", 7),
    ("12345678901234567890", 12345678901234567890),
    ("table()", {}),
    ("table(A => 1)", {"A": 1}),
    ("table(A => 1, B => 2,)", {"A": 1, "B": 2}),
    ("table(B => 1, A => 2)", {"B": 1, "A": 2}),
    (
        "table(A => table(B => table(C => 3)), D => table())",
        {"A": {"B": {"C": 3}}, "D": {}},
    ),
    ("table(_x => 1, Ab_9 => 2)", {"_x": 1, "Ab_9": 2}),
]

COMMENT_CASES = [
    ('" comment\n5', 5),
    ('5 " trailing comment', 5),
    ("|# block #| 5", 5),
    ("|#\nmulti\nline\n#|\n5", 5),
    ("table(|# a #| A |# b #| => |# c #| 1 " '" d\n)', {"A": 1}),
    ('table(A => 1, " first\n B => 2 " second\n)', {"A": 1, "B": 2}),
    ('[1 |# x #| 2 + " tail\n]', 3),
    ('def A = 1; " one\n|# two #|\n[A]', 1),
]

EXPRESSION_CASES = [
    ("[7]", 7),
    ("[1 2 +]", 3),
    ("[1 2 3 + +]", 6),
    ("[1 2 + 3 +]", 6),
    ("[2 3 pow]", 8),
    ("[2 3 pow()]", 8),
    ("[3 2 pow]", 9),
    ("[0 0 pow]", 1),
    ("[2 3 pow 1 +]", 9),
    ("[16 sqrt]", 4),
    ("[16 sqrt()]", 4),
    ("[0 sqrt]", 0),
    ("[2 sqrt]", SQRT_TWO),
    ("[9 sqrt 2 pow]", 9),
    ("[3 2 pow 4 2 pow + sqrt]", 5),
    ("[2 sqrt 2 sqrt +]", SQRT_TWO + SQRT_TWO),
]

CONSTANT_CASES = [
    ("def A = 5;\n[A]", 5),
    ("def A = 5;\ntable(X => [A])", {"X": 5}),
    ("def A = 5; def B = [A 1 +];\n[B]", 6),
    ("def A = 2; def B = [A 3 pow];\n[B A +]", 10),
    ("def A = 4;\n[A sqrt]", 2),
    ("def A = 3; table(X => [A 1 +], Y => [A 2 pow])", {"X": 4, "Y": 9}),
    ("def D = table(K => 1);\n[D]", {"K": 1}),
    ("def D = table(K => 1);\ntable(L => [D], M => [D])",
     {"L": {"K": 1}, "M": {"K": 1}}),
    ("def Inner = table(V => 2); def Outer = table(I => [Inner]);\n[Outer]",
     {"I": {"V": 2}}),
    ("def _A1 = 1; def A_b = 2;\n[_A1]", 1),
    ("def N = 1; def N2 = [N 1 +]; def N3 = [N2 N +];\ntable(R => [N3])",
     {"R": 3}),
    ("def A = 1;\ntable(X => table(Y => [A 1 +]))", {"X": {"Y": 2}}),
]

SEMANTIC_ERRORS = [
    ("[X]", "undefined constant 'X'"),
    ("def A = [B]; def B = 1; [A]", "undefined constant 'B'"),
    ("def A = [A]; 1", "undefined constant 'A'"),
    ("table(K => [Missing])", "undefined constant 'Missing'"),
    ("def A = 1; def A = 2; [A]", "already defined"),
    ("table(A => 1, A => 2)", "duplicate key 'A'"),
    ("table(A => table(B => 1, B => 2))", "duplicate key 'B'"),
    ("[+]", "needs 2 operand"),
    ("[1 +]", "needs 2 operand"),
    ("[pow]", "needs 2 operand"),
    ("[1 pow]", "needs 2 operand"),
    ("[sqrt]", "needs 1 operand"),
    ("[1 2]", "exactly one value"),
    ("[1 2 3 +]", "exactly one value"),
    ("def D = table(); [D 1 +]", "requires numbers"),
    ("def D = table(); [1 D pow]", "requires numbers"),
    ("def D = table(); [D sqrt]", "requires numbers"),
    ("[2 sqrt 10000 pow]", "cannot compute"),
]


@pytest.mark.parametrize("source, expected", VALUE_CASES)
def test_values(source, expected):
    """Numbers and dictionaries, including nested ones."""
    assert translate(source) == expected


@pytest.mark.parametrize("source, expected", COMMENT_CASES)
def test_comments_are_ignored(source, expected):
    """Both kinds of comments are skipped everywhere."""
    assert translate(source) == expected


@pytest.mark.parametrize("source, expected", EXPRESSION_CASES)
def test_postfix_expressions(source, expected):
    """The operations +, pow() and sqrt() in postfix notation."""
    assert translate(source) == expected


@pytest.mark.parametrize("source, expected", CONSTANT_CASES)
def test_constants(source, expected):
    """Declaration and evaluation of constants at translation time."""
    assert translate(source) == expected


def test_perfect_square_gives_integer():
    """The square root of a perfect square is an exact integer."""
    assert isinstance(translate("[49 sqrt]"), int)


def test_other_square_root_gives_float():
    """The square root of a non-square is a floating point number."""
    assert isinstance(translate("[2 sqrt]"), float)


def test_pow_operand_order():
    """In "a b pow" the first operand is the base."""
    assert translate("[2 5 pow]") == translate("[32]")
    assert translate("[5 2 pow]") == translate("[25]")


@pytest.mark.parametrize("source, fragment", SEMANTIC_ERRORS)
def test_semantic_errors(source, fragment):
    """Evaluation problems are reported with a clear message."""
    with pytest.raises(ConfigSemanticError) as info:
        translate(source)
    assert fragment in str(info.value)


def test_semantic_error_has_position():
    """A semantic error points to the offending token."""
    with pytest.raises(ConfigSemanticError) as info:
        translate("table(\n  A => [X]\n)")
    assert str(info.value).startswith("error at line 2, column 9")


def test_constant_cannot_see_later_constants():
    """Constants are visible only after their declaration."""
    with pytest.raises(ConfigError):
        translate("def A = [B]; def B = 1; [A]")


def test_deep_nesting_is_reported():
    """Extremely deep nesting becomes an error, not a crash."""
    depth = 5000
    source = "table(A => " * depth + "1" + ")" * depth
    with pytest.raises(ConfigError):
        translate(source)