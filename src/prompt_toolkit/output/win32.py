from __future__ import annotations
import sys
assert sys.platform == 'win32'
import os
from ctypes import ArgumentError, byref, c_char, c_long, c_uint, c_ulong, pointer
from ctypes.wintypes import DWORD, HANDLE
from typing import Callable, TextIO, TypeVar
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.data_structures import Size
from prompt_toolkit.styles import ANSI_COLOR_NAMES, Attrs
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.win32_types import CONSOLE_SCREEN_BUFFER_INFO, COORD, SMALL_RECT, STD_INPUT_HANDLE, STD_OUTPUT_HANDLE
from ..utils import SPHINX_AUTODOC_RUNNING
from .base import Output
from .color_depth import ColorDepth
if not SPHINX_AUTODOC_RUNNING:
    from ctypes import windll
__all__ = ['Win32Output']


def _coord_byval(coord: COORD) ->c_long:
    """
    Turns a COORD object into a c_long.
    This will cause it to be passed by value instead of by reference. (That is what I think at least.)

    When running ``ptipython`` is run (only with IPython), we often got the following error::

         Error in 'SetConsoleCursorPosition'.
         ArgumentError("argument 2: <class 'TypeError'>: wrong type",)
     argument 2: <class 'TypeError'>: wrong type

    It was solved by turning ``COORD`` parameters into a ``c_long`` like this.

    More info: http://msdn.microsoft.com/en-us/library/windows/desktop/ms686025(v=vs.85).aspx
    """
    return c_long(coord.Y * 0x10000 | coord.X & 0xFFFF)


_DEBUG_RENDER_OUTPUT = False
_DEBUG_RENDER_OUTPUT_FILENAME = 'prompt-toolkit-windows-output.log'


class NoConsoleScreenBufferError(Exception):
    """
    Raised when the application is not running inside a Windows Console, but
    the user tries to instantiate Win32Output.
    """

    def __init__(self) ->None:
        xterm = 'xterm' in os.environ.get('TERM', '')
        if xterm:
            message = (
                'Found %s, while expecting a Windows console. Maybe try to run this program using "winpty" or run it in cmd.exe instead. Or otherwise, in case of Cygwin, use the Python executable that is compiled for Cygwin.'
                 % os.environ['TERM'])
        else:
            message = 'No Windows console found. Are you running cmd.exe?'
        super().__init__(message)


_T = TypeVar('_T')


class Win32Output(Output):
    """
    I/O abstraction for rendering to Windows consoles.
    (cmd.exe and similar.)
    """

    def __init__(self, stdout: TextIO, use_complete_width: bool=False,
        default_color_depth: (ColorDepth | None)=None) ->None:
        self.use_complete_width = use_complete_width
        self.default_color_depth = default_color_depth
        self._buffer: list[str] = []
        self.stdout: TextIO = stdout
        self.hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))
        self._in_alternate_screen = False
        self._hidden = False
        self.color_lookup_table = ColorLookupTable()
        info = self.get_win32_screen_buffer_info()
        self.default_attrs = info.wAttributes if info else 15
        if _DEBUG_RENDER_OUTPUT:
            self.LOG = open(_DEBUG_RENDER_OUTPUT_FILENAME, 'ab')

    def fileno(self) ->int:
        """Return file descriptor."""
        return self.stdout.fileno()

    def encoding(self) ->str:
        """Return encoding used for stdout."""
        return self.stdout.encoding

    def write_raw(self, data: str) ->None:
        """For win32, there is no difference between write and write_raw."""
        self._buffer.append(data)

    def _winapi(self, func: Callable[..., _T], *a: object, **kw: object) ->_T:
        """
        Flush and call win API function.
        """
        self.flush()
        return func(*a, **kw)

    def get_win32_screen_buffer_info(self) ->CONSOLE_SCREEN_BUFFER_INFO:
        """
        Return Screen buffer info.
        """
        info = CONSOLE_SCREEN_BUFFER_INFO()
        success = self._winapi(windll.kernel32.GetConsoleScreenBufferInfo,
                               self.hconsole, byref(info))
        if success:
            return info
        else:
            raise NoConsoleScreenBufferError

    def set_title(self, title: str) ->None:
        """
        Set terminal title.
        """
        self._winapi(windll.kernel32.SetConsoleTitleW, title)

    def erase_end_of_line(self) ->None:
        """Erase from the current cursor position to the end of the line."""
        info = self.get_win32_screen_buffer_info()
        if info:
            size = info.dwSize
            cursor_pos = info.dwCursorPosition
            length = size.X - cursor_pos.X
            cells_written = c_ulong()
            self._winapi(windll.kernel32.FillConsoleOutputCharacterA,
                         self.hconsole, c_char(b' '), length,
                         _coord_byval(cursor_pos), byref(cells_written))
            self._winapi(windll.kernel32.FillConsoleOutputAttribute,
                         self.hconsole, info.wAttributes, length,
                         _coord_byval(cursor_pos), byref(cells_written))

    def reset_attributes(self) ->None:
        """Reset the console foreground/background color."""
        self._winapi(windll.kernel32.SetConsoleTextAttribute,
                     self.hconsole, self.default_attrs)

    def flush(self) ->None:
        """
        Write to output stream and flush.
        """
        if not self._buffer:
            return

        data = ''.join(self._buffer)
        self._buffer = []

        if _DEBUG_RENDER_OUTPUT:
            self.LOG.write(data.encode('utf-8', 'replace'))
            self.LOG.flush()

        self.stdout.write(data)
        self.stdout.flush()

    def scroll_buffer_to_prompt(self) ->None:
        """
        To be called before drawing the prompt. This should scroll the console
        to left, with the cursor at the bottom (if possible).
        """
        info = self.get_win32_screen_buffer_info()
        if info:
            sr = SMALL_RECT(
                Left=0,
                Top=info.srWindow.Top,
                Right=info.dwSize.X - 1,
                Bottom=info.dwSize.Y - 1,
            )
            self._winapi(windll.kernel32.SetConsoleWindowInfo,
                         self.hconsole, True, byref(sr))

            cursor_pos = COORD(x=0, y=info.dwSize.Y - 1)
            self._winapi(windll.kernel32.SetConsoleCursorPosition,
                         self.hconsole, _coord_byval(cursor_pos))

    def enter_alternate_screen(self) ->None:
        """
        Go to alternate screen buffer.
        """
        if not self._in_alternate_screen:
            self._in_alternate_screen = True
            self._winapi(windll.kernel32.SetConsoleActiveScreenBuffer,
                         self.hconsole)

    def quit_alternate_screen(self) ->None:
        """
        Make stdout again the active buffer.
        """
        if self._in_alternate_screen:
            self._in_alternate_screen = False
            self._winapi(windll.kernel32.SetConsoleActiveScreenBuffer,
                         HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)))

    @classmethod
    def win32_refresh_window(cls) ->None:
        """
        Call win32 API to refresh the whole Window.

        This is sometimes necessary when the application paints background
        for completion menus. When the menu disappears, it leaves traces due
        to a bug in the Windows Console. Sending a repaint request solves it.
        """
        hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))
        windll.user32.InvalidateRect(hconsole, None, True)

    def get_default_color_depth(self) ->ColorDepth:
        """
        Return the default color depth for a windows terminal.

        Contrary to the Vt100 implementation, this doesn't depend on a $TERM
        variable.
        """
        if self.default_color_depth is not None:
            return self.default_color_depth

        # Windows 10 supports true color.
        if sys.getwindowsversion().build >= 14393:
            return ColorDepth.DEPTH_24_BIT

        return ColorDepth.DEPTH_4_BIT


class FOREGROUND_COLOR:
    BLACK = 0
    BLUE = 1
    GREEN = 2
    CYAN = 3
    RED = 4
    MAGENTA = 5
    YELLOW = 6
    GRAY = 7
    INTENSITY = 8


class BACKGROUND_COLOR:
    BLACK = 0
    BLUE = 16
    GREEN = 32
    CYAN = 48
    RED = 64
    MAGENTA = 80
    YELLOW = 96
    GRAY = 112
    INTENSITY = 128


def _create_ansi_color_dict(color_cls: (type[FOREGROUND_COLOR] | type[
    BACKGROUND_COLOR])) ->dict[str, int]:
    """Create a table that maps the 16 named ansi colors to their Windows code."""
    return {
        'ansidefault': color_cls.GRAY,
        'ansiblack': color_cls.BLACK,
        'ansired': color_cls.RED,
        'ansigreen': color_cls.GREEN,
        'ansiyellow': color_cls.YELLOW,
        'ansiblue': color_cls.BLUE,
        'ansimagenta': color_cls.MAGENTA,
        'ansicyan': color_cls.CYAN,
        'ansigray': color_cls.GRAY,
        'ansibrightblack': color_cls.BLACK | color_cls.INTENSITY,
        'ansibrightred': color_cls.RED | color_cls.INTENSITY,
        'ansibrightgreen': color_cls.GREEN | color_cls.INTENSITY,
        'ansibrightyellow': color_cls.YELLOW | color_cls.INTENSITY,
        'ansibrightblue': color_cls.BLUE | color_cls.INTENSITY,
        'ansibrightmagenta': color_cls.MAGENTA | color_cls.INTENSITY,
        'ansibrightcyan': color_cls.CYAN | color_cls.INTENSITY,
        'ansiwhite': color_cls.GRAY | color_cls.INTENSITY,
    }


FG_ANSI_COLORS = _create_ansi_color_dict(FOREGROUND_COLOR)
BG_ANSI_COLORS = _create_ansi_color_dict(BACKGROUND_COLOR)
assert set(FG_ANSI_COLORS) == set(ANSI_COLOR_NAMES)
assert set(BG_ANSI_COLORS) == set(ANSI_COLOR_NAMES)


class ColorLookupTable:
    """
    Inspired by pygments/formatters/terminal256.py
    """

    def __init__(self) ->None:
        self._win32_colors = self._build_color_table()
        self.best_match: dict[str, tuple[int, int]] = {}

    @staticmethod
    def _build_color_table() ->list[tuple[int, int, int, int, int]]:
        """
        Build an RGB-to-256 color conversion table
        """
        pass

    def lookup_fg_color(self, fg_color: str) ->int:
        """
        Return the color for use in the
        `windll.kernel32.SetConsoleTextAttribute` API call.

        :param fg_color: Foreground as text. E.g. 'ffffff' or 'red'
        """
        pass

    def lookup_bg_color(self, bg_color: str) ->int:
        """
        Return the color for use in the
        `windll.kernel32.SetConsoleTextAttribute` API call.

        :param bg_color: Background as text. E.g. 'ffffff' or 'red'
        """
        pass
