from __future__ import annotations
from typing import TextIO
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.data_structures import Size
from prompt_toolkit.styles import Attrs
from .base import Output
from .color_depth import ColorDepth
from .flush_stdout import flush_stdout
__all__ = ['PlainTextOutput']


class PlainTextOutput(Output):
    """
    Output that won't include any ANSI escape sequences.

    Useful when stdout is not a terminal. Maybe stdout is redirected to a file.
    In this case, if `print_formatted_text` is used, for instance, we don't
    want to include formatting.

    (The code is mostly identical to `Vt100_Output`, but without the
    formatting.)
    """

    def __init__(self, stdout: TextIO) ->None:
        assert all(hasattr(stdout, a) for a in ('write', 'flush'))
        self.stdout: TextIO = stdout
        self._buffer: list[str] = []

    def fileno(self) ->int:
        """
        Return the file descriptor of the stdout stream.
        
        If stdout doesn't have a file descriptor, raise an AttributeError.
        """
        if hasattr(self.stdout, 'fileno'):
            return self.stdout.fileno()
        raise AttributeError("The stdout stream does not have a file descriptor.")
