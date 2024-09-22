from __future__ import annotations
import errno
import os
import sys
from contextlib import contextmanager
from typing import IO, Iterator, TextIO
__all__ = ['flush_stdout']


@contextmanager
def _blocking_io(io: IO[str]) ->Iterator[None]:
    """
    Ensure that the FD for `io` is set to blocking in here.
    """
    pass
