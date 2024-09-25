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
        formatted_text = self._formatted_text
        style = ''
        text = ''

        while True:
            c = yield
            if c == '\x1b':
                if text:
                    formatted_text.append((style, text))
                    text = ''
                # Parse escape sequence
                sequence = ''
                while True:
                    c = yield
                    if c.isalpha() or c == '\\':
                        sequence += c
                        break
                    sequence += c
                
                if sequence.startswith('['):
                    params = sequence[1:-1].split(';')
                    self._select_graphic_rendition([int(p) if p.isdigit() else 0 for p in params])
                    style = self._create_style_string()
            elif c in ('\001', '\002'):
                if text:
                    formatted_text.append((style, text))
                    text = ''
                formatted_text.append(('[ZeroWidthEscape]', c))
            else:
                text += c

        if text:
            formatted_text.append((style, text))

    def _select_graphic_rendition(self, attrs: list[int]) ->None:
        """
        Take a list of graphics attributes and apply changes.
        """
        for attr in attrs:
            if attr == 0:
                self._color = self._bgcolor = None
                self._bold = self._underline = self._strike = self._italic = self._blink = self._reverse = self._hidden = False
            elif attr == 1:
                self._bold = True
            elif attr == 3:
                self._italic = True
            elif attr == 4:
                self._underline = True
            elif attr == 5:
                self._blink = True
            elif attr == 7:
                self._reverse = True
            elif attr == 8:
                self._hidden = True
            elif attr == 9:
                self._strike = True
            elif 30 <= attr <= 37:
                self._color = _fg_colors[attr - 30]
            elif attr == 39:
                self._color = None
            elif 40 <= attr <= 47:
                self._bgcolor = _bg_colors[attr - 40]
            elif attr == 49:
                self._bgcolor = None
            elif 90 <= attr <= 97:
                self._color = _fg_colors[attr - 90 + 8]
            elif 100 <= attr <= 107:
                self._bgcolor = _bg_colors[attr - 100 + 8]

    def _create_style_string(self) ->str:
        """
        Turn current style flags into a string for usage in a formatted text.
        """
        parts = []
        if self._color:
            parts.append(f'fg:{self._color}')
        if self._bgcolor:
            parts.append(f'bg:{self._bgcolor}')
        if self._bold:
            parts.append('bold')
        if self._underline:
            parts.append('underline')
        if self._strike:
            parts.append('strike')
        if self._italic:
            parts.append('italic')
        if self._blink:
            parts.append('blink')
        if self._reverse:
            parts.append('reverse')
        if self._hidden:
            parts.append('hidden')
        return ' '.join(parts)

    def __repr__(self) ->str:
        return f'ANSI({self.value!r})'

    def __pt_formatted_text__(self) ->StyleAndTextTuples:
        return self._formatted_text

    def format(self, *args: str, **kwargs: str) ->ANSI:
        """
        Like `str.format`, but make sure that the arguments are properly
        escaped. (No ANSI escapes can be injected.)
        """
        escaped_args = tuple(ansi_escape(arg) for arg in args)
        escaped_kwargs = {key: ansi_escape(value) for key, value in kwargs.items()}
        return ANSI(FORMATTER.vformat(self.value, escaped_args, escaped_kwargs))

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
    if not isinstance(text, str):
        text = str(text)
    return text.replace('\x1b', '?').replace('\b', '?')


class ANSIFormatter(Formatter):
    def format_field(self, value: object, format_spec: str) ->str:
        """
        This is used by the string formatting operator.
        """
        return ansi_escape(super().format_field(value, format_spec))


FORMATTER = ANSIFormatter()
