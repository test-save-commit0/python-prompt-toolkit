from __future__ import annotations
import sys
assert sys.platform == 'win32'
from contextlib import contextmanager
from ctypes import windll
from ctypes.wintypes import HANDLE
from typing import Callable, ContextManager, Iterator
from prompt_toolkit.eventloop.win32 import create_win32_event
from ..key_binding import KeyPress
from ..utils import DummyContext
from .base import PipeInput
from .vt100_parser import Vt100Parser
from .win32 import _Win32InputBase, attach_win32_input, detach_win32_input
__all__ = ['Win32PipeInput']


class Win32PipeInput(_Win32InputBase, PipeInput):
    """
    This is an input pipe that works on Windows.
    Text or bytes can be feed into the pipe, and key strokes can be read from
    the pipe. This is useful if we want to send the input programmatically into
    the application. Mostly useful for unit testing.

    Notice that even though it's Windows, we use vt100 escape sequences over
    the pipe.

    Usage::

        input = Win32PipeInput()
        input.send_text('inputdata')
    """
    _id = 0

    def __init__(self, _event: HANDLE) ->None:
        super().__init__()
        self._event = create_win32_event()
        self._closed = False
        self._buffer: list[KeyPress] = []
        self.vt100_parser = Vt100Parser(lambda key: self._buffer.append(key))
        self.__class__._id += 1
        self._id = self.__class__._id

    def fileno(self) ->int:
        """
        The windows pipe doesn't depend on the file handle.
        """
        return -1  # Return a dummy value since it's not used

    @property
    def handle(self) ->HANDLE:
        """The handle used for registering this pipe in the event loop."""
        return self._event

    def attach(self, input_ready_callback: Callable[[], None]
        ) ->ContextManager[None]:
        """
        Return a context manager that makes this input active in the current
        event loop.
        """
        return attach_win32_input(self, input_ready_callback)

    def detach(self) ->ContextManager[None]:
        """
        Return a context manager that makes sure that this input is not active
        in the current event loop.
        """
        return detach_win32_input(self)

    def read_keys(self) ->list[KeyPress]:
        """Read list of KeyPress."""
        result = self._buffer
        self._buffer = []
        return result

    def flush_keys(self) ->list[KeyPress]:
        """
        Flush pending keys and return them.
        (Used for flushing the 'escape' key.)
        """
        return self.read_keys()

    def send_bytes(self, data: bytes) ->None:
        """Send bytes to the input."""
        self.vt100_parser.feed(data)
        windll.kernel32.SetEvent(self._event)

    def send_text(self, text: str) ->None:
        """Send text to the input."""
        self.send_bytes(text.encode())

    def close(self) ->None:
        """Close write-end of the pipe."""
        if not self._closed:
            self._closed = True
            windll.kernel32.CloseHandle(self._event)

    def typeahead_hash(self) ->str:
        """
        This needs to be unique for every `PipeInput`.
        """
        return f'win32-pipe-input-{self._id}'
