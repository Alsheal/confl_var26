"""Evaluation of the syntax tree: constants and postfix expressions."""

import math
import operator
from typing import Any, Callable, Dict, List, Tuple, Union

from lark import Token, Tree

from confl.errors import ConfigSemanticError

Number = Union[int, float]

UNARY_ARITY = 1
BINARY_ARITY = 2
SINGLE_RESULT = 1


def power(base: Number, exponent: Number) -> Number:
    """Raise ``base`` to the power ``exponent`` (the pow() function)."""
    return base ** exponent


def square_root(value: Number) -> Number:
    """Return the square root (the sqrt() function).

    The result is an exact integer when ``value`` is a perfect square.
    """
    if isinstance(value, int):
        root = math.isqrt(value)
        if root * root == value:
            return root
    return math.sqrt(value)


OPERATORS: Dict[str, Tuple[int, Callable[..., Number]]] = {
    "PLUS": (BINARY_ARITY, operator.add),
    "POW": (BINARY_ARITY, power),
    "SQRT": (UNARY_ARITY, square_root),
}


def error_at(message: str, token: Token) -> ConfigSemanticError:
    """Create a semantic error positioned at the given token."""
    return ConfigSemanticError(message, token.line, token.column)


def check_numbers(operands: List[Any], token: Token) -> None:
    """Make sure that every operand of an operation is a number."""
    for operand in operands:
        if not isinstance(operand, (int, float)):
            raise error_at(
                f"operation {str(token)!r} requires numbers, "
                "but got a dictionary",
                token,
            )


def compute(
    function: Callable[..., Number], operands: List[Any], token: Token
) -> Number:
    """Apply an operation, converting arithmetic failures to errors."""
    try:
        return function(*operands)
    except (ArithmeticError, ValueError) as error:
        raise error_at(
            f"cannot compute {str(token)!r}: {error}", token
        ) from error


def apply_operator(token: Token, stack: List[Any]) -> None:
    """Apply the operation named by ``token`` to the top of the stack."""
    arity, function = OPERATORS[token.type]
    if len(stack) < arity:
        raise error_at(
            f"operation {str(token)!r} needs {arity} operand(s), "
            f"but the stack holds {len(stack)}",
            token,
        )
    operands = stack[-arity:]
    del stack[-arity:]
    check_numbers(operands, token)
    stack.append(compute(function, operands, token))


class Evaluator:
    """Evaluates a parsed program.

    Constants are translation-time values: they are declared with
    ``def`` and substituted wherever a constant expression refers to
    them. A constant may only use constants declared before it.
    """

    def __init__(self) -> None:
        """Create an evaluator without any declared constants."""
        self._constants: Dict[str, Any] = {}

    def evaluate(self, tree: Tree) -> Any:
        """Process all definitions and return the value of the root."""
        *definitions, root = tree.children
        for definition in definitions:
            self._define(definition)
        return self._value(root)

    def _define(self, definition: Tree) -> None:
        """Evaluate a ``def`` declaration and remember the constant."""
        name, value_node = definition.children
        if str(name) in self._constants:
            raise error_at(f"constant {str(name)!r} is already defined", name)
        self._constants[str(name)] = self._value(value_node)

    def _value(self, node: Tree) -> Any:
        """Evaluate any value node of the syntax tree."""
        handlers = {
            "number": self._number,
            "dict": self._dict,
            "const_expr": self._const_expr,
        }
        return handlers[node.data](node)

    def _number(self, node: Tree) -> int:
        """Evaluate a number literal."""
        return int(node.children[0])

    def _dict(self, node: Tree) -> Dict[str, Any]:
        """Evaluate a dictionary, keeping the order of its entries."""
        result: Dict[str, Any] = {}
        for entry in node.children:
            key, value_node = entry.children
            if str(key) in result:
                raise error_at(f"duplicate key {str(key)!r}", key)
            result[str(key)] = self._value(value_node)
        return result

    def _const_expr(self, node: Tree) -> Any:
        """Evaluate a postfix constant expression with a stack."""
        stack: List[Any] = []
        for token in node.children:
            self._step(token, stack)
        if len(stack) != SINGLE_RESULT:
            raise error_at(
                "an expression must produce exactly one value, "
                f"but it produced {len(stack)}",
                node.children[0],
            )
        return stack.pop()

    def _step(self, token: Token, stack: List[Any]) -> None:
        """Process one element of a postfix expression."""
        if token.type == "NUMBER":
            stack.append(int(token))
        elif token.type == "NAME":
            stack.append(self._lookup(token))
        else:
            apply_operator(token, stack)

    def _lookup(self, token: Token) -> Any:
        """Return the value of a declared constant."""
        try:
            return self._constants[str(token)]
        except KeyError:
            raise error_at(
                f"undefined constant {str(token)!r}", token
            ) from None