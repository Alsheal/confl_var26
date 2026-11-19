"""Translation of source text into JSON."""

import json
from typing import Any

from confl.errors import ConfigSemanticError
from confl.evaluator import Evaluator
from confl.parser import parse

JSON_INDENT = 2
TOO_DEEP = "the nesting of the configuration is too deep"


def translate(text: str) -> Any:
    """Parse and evaluate the source text.

    Returns:
        The value of the root: an int, a float or a dict.

    Raises:
        ConfigError: on syntax errors and on evaluation errors.
    """
    try:
        return Evaluator().evaluate(parse(text))
    except RecursionError as error:
        raise ConfigSemanticError(TOO_DEEP) from error


def to_json(data: Any) -> str:
    """Serialize an evaluated value as indented JSON text."""
    try:
        return json.dumps(data, indent=JSON_INDENT, allow_nan=False)
    except RecursionError as error:
        raise ConfigSemanticError(TOO_DEEP) from error
    except ValueError as error:
        raise ConfigSemanticError(
            f"the result cannot be written as JSON: {error}"
        ) from error


def convert(text: str) -> str:
    """Translate the source text into JSON text."""
    return to_json(translate(text))