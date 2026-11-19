"""Parsing of the source text into a syntax tree with the Lark library."""

from typing import Optional

from lark import Lark, Tree
from lark.exceptions import (
    UnexpectedCharacters,
    UnexpectedInput,
    UnexpectedToken,
)

from confl.errors import ConfigSyntaxError
from confl.grammar import GRAMMAR

END_OF_INPUT = "$END"
COMMENT_OPEN_CHAR = "|"
UNKNOWN_POSITION = 0

TERMINAL_NAMES = {
    "_DEF": "'def'",
    "_TABLE": "'table'",
    "_EQ": "'='",
    "_ARROW": "'=>'",
    "_SEMI": "';'",
    "_COMMA": "','",
    "_LPAR": "'('",
    "_RPAR": "')'",
    "_LSQB": "'['",
    "_RSQB": "']'",
    "PLUS": "'+'",
    "POW": "'pow()'",
    "SQRT": "'sqrt()'",
    "NAME": "name",
    "NUMBER": "number",
    END_OF_INPUT: "end of input",
}

PARSER = Lark(GRAMMAR, parser="lalr", start="start")


def display_name(terminal: str) -> str:
    """Return a human readable name of a grammar terminal."""
    return TERMINAL_NAMES.get(terminal, terminal)


def describe_unexpected_char(error: UnexpectedCharacters) -> str:
    """Build the message for a character that no token can start with."""
    message = f"unexpected character {error.char!r}"
    if error.char == COMMENT_OPEN_CHAR:
        message += " (is a '|#' comment missing its closing '#|'?)"
    return message


def describe_unexpected_token(error: UnexpectedToken) -> str:
    """Build the message for a token that is not allowed at this place."""
    expected = sorted(display_name(name) for name in error.expected)
    options = ", ".join(expected)
    if error.token.type == END_OF_INPUT:
        found = "unexpected end of input"
    else:
        found = f"unexpected {display_name(error.token.type)}"
        found += f" {str(error.token)!r}"
    return f"{found}; expected one of: {options}"


def describe(error: UnexpectedInput) -> str:
    """Turn a Lark parsing exception into a readable message."""
    if isinstance(error, UnexpectedCharacters):
        return describe_unexpected_char(error)
    if isinstance(error, UnexpectedToken):
        return describe_unexpected_token(error)
    return "unexpected end of input"


def known_position(value: Optional[int]) -> Optional[int]:
    """Return the position or None when Lark could not determine it."""
    if value is None or value <= UNKNOWN_POSITION:
        return None
    return value


def parse(text: str) -> Tree:
    """Parse the source text and return its syntax tree.

    Raises:
        ConfigSyntaxError: if the text violates the grammar.
    """
    try:
        return PARSER.parse(text)
    except UnexpectedInput as error:
        raise ConfigSyntaxError(
            describe(error),
            known_position(getattr(error, "line", None)),
            known_position(getattr(error, "column", None)),
        ) from error