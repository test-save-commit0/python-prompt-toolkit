from __future__ import annotations
from string import Formatter
from typing import Generator
from prompt_toolkit.output.vt100 import BG_ANSI_COLORS, FG_ANSI_COLORS
from prompt_toolkit.output.vt100 import _256_colors as _256_colors_table
from .base import StyleAndTextTuples
__all__ = ['ANSI', 'ansi_escape']


class ANSI:
    """
    ANSI formatted text.
    Take something ANSI escaped text, for use as a formatted string. E.g.

    ::

        ANSI('\\x1b[31mhello \\x1b[32mworld')

    Characters between ``\\001`` and ``\\002`` are supposed to have a zero width
    when printed, but these are literally sent to the terminal output. This can
    be used for instance, for inserting Final Term prompt commands.  They will
    be translated into a prompt_toolkit '[ZeroWidthEscape]' fragment.
    """

    def __init__(self, value: str) ->None:
        self.value = value
        self._formatted_text: StyleAndTextTuples = []
        self._color: str | None = None
        self._bgcolor: str | None = None
        self._bold = False
        self._underline = False
        self._strike = False
        self._italic = False
        self._blink = False
        self._reverse = False
        self._hidden = False
        parser = self._parse_corot()
        parser.send(None)
        for c in value:
            parser.send(c)

    def _parse_corot(self) ->Generator[None, str, None]:
        """
        Coroutine that parses the ANSI escape sequences.
        """
        pass

    def _select_graphic_rendition(self, attrs: list[int]) ->None:
        """
        Taken a list of graphics attributes and apply changes.
        """
        pass

    def _create_style_string(self) ->str:
        """
        Turn current style flags into a string for usage in a formatted text.
        """
        pass

    def __repr__(self) ->str:
        return f'ANSI({self.value!r})'

    def __pt_formatted_text__(self) ->StyleAndTextTuples:
        return self._formatted_text

    def format(self, *args: str, **kwargs: str) ->ANSI:
        """
        Like `str.format`, but make sure that the arguments are properly
        escaped. (No ANSI escapes can be injected.)
        """
        pass

    def __mod__(self, value: object) ->ANSI:
        """
        ANSI('<b>%s</b>') % value
        """
        if not isinstance(value, tuple):
            value = value,
        value = tuple(ansi_escape(i) for i in value)
        return ANSI(self.value % value)


_fg_colors = {v: k for k, v in FG_ANSI_COLORS.items()}
_bg_colors = {v: k for k, v in BG_ANSI_COLORS.items()}
_256_colors = {}
for i, (r, g, b) in enumerate(_256_colors_table.colors):
    _256_colors[i] = f'#{r:02x}{g:02x}{b:02x}'


def ansi_escape(text: object) ->str:
    """
    Replace characters with a special meaning.
    """
    pass


class ANSIFormatter(Formatter):
    pass


FORMATTER = ANSIFormatter()
