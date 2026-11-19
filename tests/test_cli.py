"""Tests of the command line interface."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from confl.cli import EXIT_FAILURE, EXIT_OK, main

SOURCE_DIR = Path(__file__).resolve().parent.parent / "src"
SAMPLE = 'table(A => [2 3 pow], B => table(C => 1))'
SAMPLE_RESULT = {"A": 8, "B": {"C": 1}}


def write(tmp_path, text):
    """Create a configuration file and return its path as a string."""
    path = tmp_path / "config.confl"
    path.write_text(text, encoding="utf-8")
    return str(path)


def test_success_writes_json_to_stdout(tmp_path, capsys):
    """A valid file is translated into JSON on standard output."""
    code = main(["-i", write(tmp_path, SAMPLE)])
    captured = capsys.readouterr()
    assert code == EXIT_OK
    assert json.loads(captured.out) == SAMPLE_RESULT
    assert captured.err == ""


def test_long_option_name(tmp_path, capsys):
    """The key is available as --input."""
    code = main(["--input", write(tmp_path, SAMPLE)])
    assert code == EXIT_OK
    assert json.loads(capsys.readouterr().out) == SAMPLE_RESULT


def test_utf8_comments(tmp_path, capsys):
    """Comments in Russian are read correctly."""
    text = '" Комментарий\n|# Многострочный\nкомментарий #|\ntable(A => 1)'
    code = main(["-i", write(tmp_path, text)])
    assert code == EXIT_OK
    assert json.loads(capsys.readouterr().out) == {"A": 1}


def test_syntax_error_is_reported(tmp_path, capsys):
    """A syntax error gives a message on stderr and a failure code."""
    code = main(["-i", write(tmp_path, "table(A => )")])
    captured = capsys.readouterr()
    assert code == EXIT_FAILURE
    assert captured.out == ""
    assert "syntax error at line 1" in captured.err


def test_semantic_error_is_reported(tmp_path, capsys):
    """An evaluation error gives a message on stderr."""
    code = main(["-i", write(tmp_path, "[Unknown]")])
    captured = capsys.readouterr()
    assert code == EXIT_FAILURE
    assert captured.out == ""
    assert "undefined constant 'Unknown'" in captured.err


def test_missing_file(tmp_path, capsys):
    """A file that does not exist is reported."""
    code = main(["-i", str(tmp_path / "absent.confl")])
    captured = capsys.readouterr()
    assert code == EXIT_FAILURE
    assert "cannot read the file" in captured.err


def test_invalid_encoding(tmp_path, capsys):
    """A file that is not UTF-8 text is reported."""
    path = tmp_path / "binary.confl"
    path.write_bytes(b"\xff\xfe\x00")
    code = main(["-i", str(path)])
    assert code == EXIT_FAILURE
    assert "cannot read the file" in capsys.readouterr().err


def test_input_key_is_required():
    """Running without -i is a usage error."""
    with pytest.raises(SystemExit) as info:
        main([])
    assert info.value.code != EXIT_OK


def test_version_key(capsys):
    """The --version key prints the program version."""
    with pytest.raises(SystemExit) as info:
        main(["--version"])
    assert info.value.code == EXIT_OK
    assert capsys.readouterr().out.startswith("confl ")


def test_module_entry_point(tmp_path):
    """The tool can be started as "python -m confl"."""
    environment = dict(os.environ, PYTHONPATH=str(SOURCE_DIR))
    completed = subprocess.run(
        [sys.executable, "-m", "confl", "-i", write(tmp_path, SAMPLE)],
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    assert completed.returncode == EXIT_OK
    assert json.loads(completed.stdout) == SAMPLE_RESULT