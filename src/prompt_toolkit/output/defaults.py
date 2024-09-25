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
    if stdout is None:
        stdout = sys.stdout

    # Check if the output is a TTY.
    if not stdout.isatty() and always_prefer_tty:
        stdout = sys.stderr

    if not stdout.isatty():
        return PlainTextOutput(stdout)

    term = get_term_environment_variable()
    bell_variable = get_bell_environment_variable()

    # If the PROMPT_TOOLKIT_COLOR_DEPTH environment variable is set, use that.
    color_depth = ColorDepth.default()

    if is_conemu_ansi():
        from .conemu import ConEmuOutput
        return ConEmuOutput(stdout)

    if term in ('linux', 'eterm-color'):
        from .vt100 import Vt100_Output
        return Vt100_Output(stdout, color_depth=color_depth)

    if term == 'windows':
        from .win32 import Win32Output
        return Win32Output(stdout, bell_variable=bell_variable)

    # Default to VT100 output.
    from .vt100 import Vt100_Output
    return Vt100_Output(stdout, color_depth=color_depth)
