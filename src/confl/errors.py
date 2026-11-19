"""Exception types raised by the configuration language translator."""

from typing import Optional


class ConfigError(Exception):
    """Base class for all translator errors.

    Attributes:
        message: Human readable description of the problem.
        line: One-based line number, or None when it is unknown.
        column: One-based column number, or None when it is unknown.
    """

    label = "error"

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        column: Optional[int] = None,
    ) -> None:
        """Store the message together with the source position."""
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column

    def __str__(self) -> str:
        """Format the error with its source position when available."""
        if self.line is None or self.column is None:
            return f"{self.label}: {self.message}"
        position = f"line {self.line}, column {self.column}"
        return f"{self.label} at {position}: {self.message}"


class ConfigSyntaxError(ConfigError):
    """The input text does not conform to the language grammar."""

    label = "syntax error"


class ConfigSemanticError(ConfigError):
    """The input is well-formed but cannot be evaluated."""

    label = "error"