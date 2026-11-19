"""Command line interface of the translator."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from confl import __version__
from confl.converter import convert
from confl.errors import ConfigError

EXIT_OK = 0
EXIT_FAILURE = 1
PROG_NAME = "confl"


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser of the command line tool."""
    parser = argparse.ArgumentParser(
        prog=PROG_NAME,
        description=(
            "Translate a configuration written in the educational "
            "language into JSON. The JSON is written to standard output."
        ),
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        metavar="FILE",
        help="path to the file with the configuration text",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def read_source(path: str) -> str:
    """Read the configuration text from a UTF-8 encoded file."""
    return Path(path).read_text(encoding="utf-8")


def report(path: str, message: object) -> int:
    """Print an error message to standard error and return its code."""
    print(f"{PROG_NAME}: {path}: {message}", file=sys.stderr)
    return EXIT_FAILURE


def main(argv: Optional[List[str]] = None) -> int:
    """Run the tool and return the process exit code."""
    args = build_parser().parse_args(argv)
    try:
        output = convert(read_source(args.input))
    except (OSError, UnicodeDecodeError) as error:
        return report(args.input, f"cannot read the file: {error}")
    except ConfigError as error:
        return report(args.input, error)
    print(output)
    return EXIT_OK