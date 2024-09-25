from __future__ import annotations
import io
import sys
from typing import ContextManager, TextIO
from .base import DummyInput, Input, PipeInput
__all__ = ['create_input', 'create_pipe_input']


def create_input(stdin: (TextIO | None)=None, always_prefer_tty: bool=False
    ) ->Input:
    """
    Create the appropriate `Input` object for the current os/environment.

    :param always_prefer_tty: When set, if `sys.stdin` is connected to a Unix
        `pipe`, check whether `sys.stdout` or `sys.stderr` are connected to a
        pseudo terminal. If so, open the tty for reading instead of reading for
        `sys.stdin`. (We can open `stdout` or `stderr` for reading, this is how
        a `$PAGER` works.)
    """
    if stdin is None:
        stdin = sys.stdin

    if sys.platform == 'win32':
        from prompt_toolkit.input.win32 import Win32Input
        return Win32Input(stdin)
    else:
        from prompt_toolkit.input.vt100 import Vt100Input
        if always_prefer_tty and not stdin.isatty():
            for file in (sys.stderr, sys.stdout):
                if file.isatty():
                    return Vt100Input(open(file.fileno(), 'rb', buffering=0))
        return Vt100Input(stdin)


def create_pipe_input() ->ContextManager[PipeInput]:
    """
    Create an input pipe.
    This is mostly useful for unit testing.

    Usage::

        with create_pipe_input() as input:
            input.send_text('inputdata')

    Breaking change: In prompt_toolkit 3.0.28 and earlier, this was returning
    the `PipeInput` directly, rather than through a context manager.
    """
    return _PipeInputContextManager()

class _PipeInputContextManager:
    def __enter__(self) -> PipeInput:
        self.pipe_input = PipeInput()
        return self.pipe_input

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pipe_input.close()
