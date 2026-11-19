"""Tests of the grammar: accepted constructs and syntax errors."""

import pytest

from confl.errors import ConfigSyntaxError
from confl.parser import parse

VALID_SOURCES = [
    "0",
    "007",
    "table()",
    "table(A => 1)",
    "table(A => 1, B => 2, C => 3)",
    "table(A => 1,)",
    "table(\n  A => 1,\n  B => 2,\n)",
    "table(A => table(B => table(C => 3)))",
    "table(_x => 1, Ab_9 => 2, _ => 3, Z => 4)",
    "[1]",
    "[A 1 +]",
    "[2 3 pow]",
    "[2 3 pow()]",
    "[16 sqrt]",
    "[16 sqrt()]",
    "[1 2 3 + +]",
    "def A = 1;\n[A]",
    "def A = 1; def B = [A 1 +]; table(X => [B])",
    "def D = table(K => 1);\n[D]",
    '" comment\n5',
    '5 " comment without a final newline',
    '" Комментарий на русском языке\n5',
    '" def A = 1; |# not a block comment\n5',
    "|# block comment #| 5",
    "|#\nmulti\nline\ncomment\n#|\n5",
    "table(|# inside #| A |# a #| => |# b #| 1 |# c #|)",
    'table(\n  A => 1, " first\n  B => 2  " second\n)',
    '[1 |# inside an expression #| 2 + " tail\n]',
    "|# one #| |# two #| 5",
    '|# with a " quote #| 5',
]

INVALID_SOURCES = [
    "",
    "   ",
    '" only a comment',
    "|# only a comment #|",
    "def A = 1;",
    "def A = 1 [A]",
    "def a = 1; 1",
    "def A 1; 1",
    "def A = ; 1",
    "def = 1; 1",
    "table(A => )",
    "table(A 1)",
    "table(A = 1)",
    "table(A => 1 B => 2)",
    "table(A => 1,, B => 2)",
    "table(a => 1)",
    "table(1 => 1)",
    "table(A => 1",
    "table A => 1",
    "table(,)",
    "[1 2 +",
    "[]",
    "1 2",
    "table() table()",
    "|# no end 5",
    "[1 2 -]",
    "1.5",
    "-1",
    "+1",
    "0x10",
    "0b101",
    "@x",
    '@"string"',
    "[1; 2]",
    "list(1, 2)",
    "begin end",
]


@pytest.mark.parametrize("source", VALID_SOURCES)
def test_valid_source_is_parsed(source):
    """Every construct of the language is accepted."""
    assert parse(source) is not None


@pytest.mark.parametrize("source", INVALID_SOURCES)
def test_invalid_source_raises_syntax_error(source):
    """Text that violates the grammar is rejected with an error."""
    with pytest.raises(ConfigSyntaxError):
        parse(source)


def test_syntax_error_has_position():
    """A syntax error points to the line and column of the problem."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("table(\n  A => 1\n  B => 2\n)")
    assert str(info.value).startswith("syntax error at line 3, column 3")


def test_syntax_error_lists_expected_tokens():
    """The message names what was expected instead."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("table(A 1)")
    assert "'=>'" in str(info.value)


def test_unterminated_block_comment_is_explained():
    """The message hints at the missing closing #| of a comment."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("|# never closed\n5")
    assert "#|" in str(info.value)


def test_end_of_input_is_reported():
    """An unexpected end of the text is reported as such."""
    with pytest.raises(ConfigSyntaxError) as info:
        parse("table(A => 1")
    assert "end of input" in str(info.value)