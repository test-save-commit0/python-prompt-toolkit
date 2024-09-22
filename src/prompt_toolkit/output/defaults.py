from __future__ import annotations
import sys
from typing import TextIO, cast
from prompt_toolkit.utils import get_bell_environment_variable, get_term_environment_variable, is_conemu_ansi
from .base import DummyOutput, Output
from .color_depth import ColorDepth
from .plain_text import PlainTextOutput
__all__ = ['create_output']


def create_output(stdout: (TextIO | None)=None, always_prefer_tty: bool=False
    ) ->Output:
    """
    Return an :class:`~prompt_toolkit.output.Output` instance for the command
    line.

    :param stdout: The stdout object
    :param always_prefer_tty: When set, look for `sys.stderr` if `sys.stdout`
        is not a TTY. Useful if `sys.stdout` is redirected to a file, but we
        still want user input and output on the terminal.

        By default, this is `False`. If `sys.stdout` is not a terminal (maybe
        it's redirected to a file), then a `PlainTextOutput` will be returned.
        That way, tools like `print_formatted_text` will write plain text into
        that file.
    """
    pass
