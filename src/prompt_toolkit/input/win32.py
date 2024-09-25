from __future__ import annotations
import os
import sys
from abc import abstractmethod
from asyncio import get_running_loop
from contextlib import contextmanager
from ..utils import SPHINX_AUTODOC_RUNNING
assert sys.platform == 'win32'
if not SPHINX_AUTODOC_RUNNING:
    import msvcrt
    from ctypes import windll
from ctypes import Array, pointer
from ctypes.wintypes import DWORD, HANDLE
from typing import Callable, ContextManager, Iterable, Iterator, TextIO
from prompt_toolkit.eventloop import run_in_executor_with_context
from prompt_toolkit.eventloop.win32 import create_win32_event, wait_for_handles
from prompt_toolkit.key_binding.key_processor import KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseButton, MouseEventType
from prompt_toolkit.win32_types import INPUT_RECORD, KEY_EVENT_RECORD, MOUSE_EVENT_RECORD, STD_INPUT_HANDLE, EventTypes
from .ansi_escape_sequences import REVERSE_ANSI_SEQUENCES
from .base import Input
__all__ = ['Win32Input', 'ConsoleInputReader', 'raw_mode', 'cooked_mode',
    'attach_win32_input', 'detach_win32_input']
FROM_LEFT_1ST_BUTTON_PRESSED = 1
RIGHTMOST_BUTTON_PRESSED = 2
MOUSE_MOVED = 1
MOUSE_WHEELED = 4


class _Win32InputBase(Input):
    """
    Base class for `Win32Input` and `Win32PipeInput`.
    """

    def __init__(self) ->None:
        self.win32_handles = _Win32Handles()


class Win32Input(_Win32InputBase):
    """
    `Input` class that reads from the Windows console.
    """

    def __init__(self, stdin: (TextIO | None)=None) ->None:
        super().__init__()
        self.console_input_reader = ConsoleInputReader()

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


class ConsoleInputReader:
    """
    :param recognize_paste: When True, try to discover paste actions and turn
        the event into a BracketedPaste.
    """
    mappings = {b'\x1b': Keys.Escape, b'\x00': Keys.ControlSpace, b'\x01':
        Keys.ControlA, b'\x02': Keys.ControlB, b'\x03': Keys.ControlC,
        b'\x04': Keys.ControlD, b'\x05': Keys.ControlE, b'\x06': Keys.
        ControlF, b'\x07': Keys.ControlG, b'\x08': Keys.ControlH, b'\t':
        Keys.ControlI, b'\n': Keys.ControlJ, b'\x0b': Keys.ControlK,
        b'\x0c': Keys.ControlL, b'\r': Keys.ControlM, b'\x0e': Keys.
        ControlN, b'\x0f': Keys.ControlO, b'\x10': Keys.ControlP, b'\x11':
        Keys.ControlQ, b'\x12': Keys.ControlR, b'\x13': Keys.ControlS,
        b'\x14': Keys.ControlT, b'\x15': Keys.ControlU, b'\x16': Keys.
        ControlV, b'\x17': Keys.ControlW, b'\x18': Keys.ControlX, b'\x19':
        Keys.ControlY, b'\x1a': Keys.ControlZ, b'\x1c': Keys.
        ControlBackslash, b'\x1d': Keys.ControlSquareClose, b'\x1e': Keys.
        ControlCircumflex, b'\x1f': Keys.ControlUnderscore, b'\x7f': Keys.
        Backspace}
    keycodes = {(33): Keys.PageUp, (34): Keys.PageDown, (35): Keys.End, (36
        ): Keys.Home, (37): Keys.Left, (38): Keys.Up, (39): Keys.Right, (40
        ): Keys.Down, (45): Keys.Insert, (46): Keys.Delete, (112): Keys.F1,
        (113): Keys.F2, (114): Keys.F3, (115): Keys.F4, (116): Keys.F5, (
        117): Keys.F6, (118): Keys.F7, (119): Keys.F8, (120): Keys.F9, (121
        ): Keys.F10, (122): Keys.F11, (123): Keys.F12}
    LEFT_ALT_PRESSED = 2
    RIGHT_ALT_PRESSED = 1
    SHIFT_PRESSED = 16
    LEFT_CTRL_PRESSED = 8
    RIGHT_CTRL_PRESSED = 4

    def __init__(self, recognize_paste: bool=True) ->None:
        self._fdcon = None
        self.recognize_paste = recognize_paste
        self.handle: HANDLE
        if sys.stdin.isatty():
            self.handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
                )
        else:
            self._fdcon = os.open('CONIN$', os.O_RDWR | os.O_BINARY)
            self.handle = HANDLE(msvcrt.get_osfhandle(self._fdcon))

    def close(self) ->None:
        """Close fdcon."""
        if self._fdcon is not None:
            os.close(self._fdcon)

    def read(self) ->Iterable[KeyPress]:
        """
        Return a list of `KeyPress` instances. It won't return anything when
        there was nothing to read.  (This function doesn't block.)

        http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
        """
        max_records = 1024
        records = (INPUT_RECORD * max_records)()
        read = DWORD()

        if windll.kernel32.ReadConsoleInputW(self.handle, records, max_records, pointer(read)):
            return list(self._get_keys(read.value, records))
        return []

    def _insert_key_data(self, key_press: KeyPress) ->KeyPress:
        """
        Insert KeyPress data, for vt100 compatibility.
        """
        if key_press.data:
            return key_press

        data = REVERSE_ANSI_SEQUENCES.get(key_press.key, '')
        return KeyPress(key_press.key, data)

    def _get_keys(self, read: DWORD, input_records: Array[INPUT_RECORD]
        ) ->Iterator[KeyPress]:
        """
        Generator that yields `KeyPress` objects from the input records.
        """
        for i in range(read):
            ir = input_records[i]

            if ir.EventType == EventTypes.KEY_EVENT:
                for key_press in self._event_to_key_presses(ir.Event.KeyEvent):
                    yield self._insert_key_data(key_press)

            elif ir.EventType == EventTypes.MOUSE_EVENT:
                for key_press in self._handle_mouse(ir.Event.MouseEvent):
                    yield key_press

            elif ir.EventType == EventTypes.WINDOW_BUFFER_SIZE_EVENT:
                yield KeyPress(Keys.WindowResize, '')

        key_presses = list(self._merge_paired_surrogates(list(self._get_keys(read, input_records))))

        if self.recognize_paste and self._is_paste(key_presses):
            yield KeyPress(Keys.BracketedPaste, ''.join(k.data for k in key_presses))
        else:
            yield from key_presses

    @staticmethod
    def _merge_paired_surrogates(key_presses: list[KeyPress]) ->Iterator[
        KeyPress]:
        """
        Combines consecutive KeyPresses with high and low surrogates into
        single characters
        """
        i = 0
        while i < len(key_presses):
            if i + 1 < len(key_presses) and \
               0xD800 <= ord(key_presses[i].data) <= 0xDBFF and \
               0xDC00 <= ord(key_presses[i + 1].data) <= 0xDFFF:
                yield KeyPress(key_presses[i].key, key_presses[i].data + key_presses[i + 1].data)
                i += 2
            else:
                yield key_presses[i]
                i += 1

    @staticmethod
    def _is_paste(keys: list[KeyPress]) ->bool:
        """
        Return `True` when we should consider this list of keys as a paste
        event. Pasted text on windows will be turned into a
        `Keys.BracketedPaste` event. (It's not 100% correct, but it is probably
        the best possible way to detect pasting of text and handle that
        correctly.)
        """
        return (
            len(keys) > 1 and
            all(k.key == Keys.ControlV or (
                not isinstance(k.key, Keys) and
                k.data is not None and
                len(k.data) == 1
            ) for k in keys)
        )

    def _event_to_key_presses(self, ev: KEY_EVENT_RECORD) ->list[KeyPress]:
        """
        For this `KEY_EVENT_RECORD`, return a list of `KeyPress` instances.
        """
        result = []

        if ev.KeyDown or ev.KeyDown == 0:  # In case of KeyUp, no unicode will be present.
            if ev.UnicodeChar == '\x00':
                if ev.VirtualKeyCode in self.keycodes:
                    result.append(KeyPress(self.keycodes[ev.VirtualKeyCode], ''))
            else:
                result.append(KeyPress(ev.UnicodeChar, ev.UnicodeChar))

        # Correctly handle Control-Arrow keys.
        if (ev.ControlKeyState & self.LEFT_CTRL_PRESSED or
            ev.ControlKeyState & self.RIGHT_CTRL_PRESSED) and ev.VirtualKeyCode in self.keycodes:
            result.append(KeyPress(self.keycodes[ev.VirtualKeyCode], ''))

        # Turn stateful shift/control/alt keys into individual events.
        for k, v in [
            (Keys.Shift, ev.ControlKeyState & self.SHIFT_PRESSED),
            (Keys.Control, ev.ControlKeyState & self.LEFT_CTRL_PRESSED),
            (Keys.Control, ev.ControlKeyState & self.RIGHT_CTRL_PRESSED),
            (Keys.Alt, ev.ControlKeyState & self.LEFT_ALT_PRESSED),
            (Keys.Alt, ev.ControlKeyState & self.RIGHT_ALT_PRESSED),
        ]:
            if v:
                result.append(KeyPress(k, ''))

        return result

    def _handle_mouse(self, ev: MOUSE_EVENT_RECORD) ->list[KeyPress]:
        """
        Handle mouse events. Return a list of KeyPress instances.
        """
        result = []

        # Get mouse position.
        position = ev.MousePosition.X, ev.MousePosition.Y

        # Mouse event.
        if ev.EventFlags in (0, MOUSE_MOVED):
            # Button press or release.
            if ev.ButtonState == FROM_LEFT_1ST_BUTTON_PRESSED:
                result.append(KeyPress(Keys.MouseDown, ''))
            elif ev.ButtonState == RIGHTMOST_BUTTON_PRESSED:
                result.append(KeyPress(Keys.MouseDown, ''))
            else:
                result.append(KeyPress(Keys.MouseUp, ''))

        elif ev.EventFlags & MOUSE_WHEELED:
            result.append(KeyPress(Keys.ScrollUp if ev.ButtonState > 0 else Keys.ScrollDown, ''))

        return result


class _Win32Handles:
    """
    Utility to keep track of which handles are connectod to which callbacks.

    `add_win32_handle` starts a tiny event loop in another thread which waits
    for the Win32 handle to become ready. When this happens, the callback will
    be called in the current asyncio event loop using `call_soon_threadsafe`.

    `remove_win32_handle` will stop this tiny event loop.

    NOTE: We use this technique, so that we don't have to use the
          `ProactorEventLoop` on Windows and we can wait for things like stdin
          in a `SelectorEventLoop`. This is important, because our inputhook
          mechanism (used by IPython), only works with the `SelectorEventLoop`.
    """

    def __init__(self) ->None:
        self._handle_callbacks: dict[int, Callable[[], None]] = {}
        self._remove_events: dict[int, HANDLE] = {}

    def add_win32_handle(self, handle: HANDLE, callback: Callable[[], None]
        ) ->None:
        """
        Add a Win32 handle to the event loop.
        """
        handle_value = handle.value

        # Create an event object.
        event = create_win32_event()
        self._remove_events[handle_value] = event

        # Add reader.
        def ready() ->None:
            del self._handle_callbacks[handle_value]
            del self._remove_events[handle_value]
            callback()

        self._handle_callbacks[handle_value] = ready

        # Start wait thread.
        def wait_for_handle() ->None:
            while True:
                result = wait_for_handles([handle, event])
                if result == 0:
                    get_running_loop().call_soon_threadsafe(ready)
                else:
                    break

        threading.Thread(target=wait_for_handle, daemon=True).start()

    def remove_win32_handle(self, handle: HANDLE) ->(Callable[[], None] | None
        ):
        """
        Remove a Win32 handle from the event loop.
        Return either the registered handler or `None`.
        """
        handle_value = handle.value

        if handle_value in self._handle_callbacks:
            callback = self._handle_callbacks.pop(handle_value)
            event = self._remove_events.pop(handle_value)
            windll.kernel32.SetEvent(event)
            return callback

        return None


@contextmanager
def attach_win32_input(input: _Win32InputBase, callback: Callable[[], None]
    ) ->Iterator[None]:
    """
    Context manager that makes this input active in the current event loop.

    :param input: :class:`~prompt_toolkit.input.Input` object.
    :param input_ready_callback: Called when the input is ready to read.
    """
    handle = input.console_input_reader.handle

    def ready() ->None:
        # When the console is ready, set the event.
        callback()

    input.win32_handles.add_win32_handle(handle, ready)

    try:
        yield
    finally:
        input.win32_handles.remove_win32_handle(handle)


class raw_mode:
    """
    ::

        with raw_mode(stdin):
            ''' the windows terminal is now in 'raw' mode. '''

    The ``fileno`` attribute is ignored. This is to be compatible with the
    `raw_input` method of `.vt100_input`.
    """

    def __init__(self, fileno: (int | None)=None) ->None:
        self.handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

    def __enter__(self) ->None:
        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(self.handle, pointer(original_mode))
        self.original_mode = original_mode
        self._patch()

    def __exit__(self, *a: object) ->None:
        windll.kernel32.SetConsoleMode(self.handle, self.original_mode)


class cooked_mode(raw_mode):
    """
    ::

        with cooked_mode(stdin):
            ''' The pseudo-terminal stdin is now used in cooked mode. '''
    """
