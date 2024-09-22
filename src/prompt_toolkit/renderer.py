"""
Renders the command line on the console.
(Redraws parts of the input line that were changed.)
"""
from __future__ import annotations
from asyncio import FIRST_COMPLETED, Future, ensure_future, sleep, wait
from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Hashable
from prompt_toolkit.application.current import get_app
from prompt_toolkit.cursor_shapes import CursorShape
from prompt_toolkit.data_structures import Point, Size
from prompt_toolkit.filters import FilterOrBool, to_filter
from prompt_toolkit.formatted_text import AnyFormattedText, to_formatted_text
from prompt_toolkit.layout.mouse_handlers import MouseHandlers
from prompt_toolkit.layout.screen import Char, Screen, WritePosition
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.styles import Attrs, BaseStyle, DummyStyleTransformation, StyleTransformation
if TYPE_CHECKING:
    from prompt_toolkit.application import Application
    from prompt_toolkit.layout.layout import Layout
__all__ = ['Renderer', 'print_formatted_text']


def _output_screen_diff(app: Application[Any], output: Output, screen:
    Screen, current_pos: Point, color_depth: ColorDepth, previous_screen: (
    Screen | None), last_style: (str | None), is_done: bool, full_screen:
    bool, attrs_for_style_string: _StyleStringToAttrsCache,
    style_string_has_style: _StyleStringHasStyleCache, size: Size,
    previous_width: int) ->tuple[Point, str | None]:
    """
    Render the diff between this screen and the previous screen.

    This takes two `Screen` instances. The one that represents the output like
    it was during the last rendering and one that represents the current
    output raster. Looking at these two `Screen` instances, this function will
    render the difference by calling the appropriate methods of the `Output`
    object that only paint the changes to the terminal.

    This is some performance-critical code which is heavily optimized.
    Don't change things without profiling first.

    :param current_pos: Current cursor position.
    :param last_style: The style string, used for drawing the last drawn
        character.  (Color/attributes.)
    :param attrs_for_style_string: :class:`._StyleStringToAttrsCache` instance.
    :param width: The width of the terminal.
    :param previous_width: The width of the terminal during the last rendering.
    """
    pass


class HeightIsUnknownError(Exception):
    """Information unavailable. Did not yet receive the CPR response."""


class _StyleStringToAttrsCache(Dict[str, Attrs]):
    """
    A cache structure that maps style strings to :class:`.Attr`.
    (This is an important speed up.)
    """

    def __init__(self, get_attrs_for_style_str: Callable[[str], Attrs],
        style_transformation: StyleTransformation) ->None:
        self.get_attrs_for_style_str = get_attrs_for_style_str
        self.style_transformation = style_transformation

    def __missing__(self, style_str: str) ->Attrs:
        attrs = self.get_attrs_for_style_str(style_str)
        attrs = self.style_transformation.transform_attrs(attrs)
        self[style_str] = attrs
        return attrs


class _StyleStringHasStyleCache(Dict[str, bool]):
    """
    Cache for remember which style strings don't render the default output
    style (default fg/bg, no underline and no reverse and no blink). That way
    we know that we should render these cells, even when they're empty (when
    they contain a space).

    Note: we don't consider bold/italic/hidden because they don't change the
    output if there's no text in the cell.
    """

    def __init__(self, style_string_to_attrs: dict[str, Attrs]) ->None:
        self.style_string_to_attrs = style_string_to_attrs

    def __missing__(self, style_str: str) ->bool:
        attrs = self.style_string_to_attrs[style_str]
        is_default = bool(attrs.color or attrs.bgcolor or attrs.underline or
            attrs.strike or attrs.blink or attrs.reverse)
        self[style_str] = is_default
        return is_default


class CPR_Support(Enum):
    """Enum: whether or not CPR is supported."""
    SUPPORTED = 'SUPPORTED'
    NOT_SUPPORTED = 'NOT_SUPPORTED'
    UNKNOWN = 'UNKNOWN'


class Renderer:
    """
    Typical usage:

    ::

        output = Vt100_Output.from_pty(sys.stdout)
        r = Renderer(style, output)
        r.render(app, layout=...)
    """
    CPR_TIMEOUT = 2

    def __init__(self, style: BaseStyle, output: Output, full_screen: bool=
        False, mouse_support: FilterOrBool=False,
        cpr_not_supported_callback: (Callable[[], None] | None)=None) ->None:
        self.style = style
        self.output = output
        self.full_screen = full_screen
        self.mouse_support = to_filter(mouse_support)
        self.cpr_not_supported_callback = cpr_not_supported_callback
        self._in_alternate_screen = False
        self._mouse_support_enabled = False
        self._bracketed_paste_enabled = False
        self._cursor_key_mode_reset = False
        self._waiting_for_cpr_futures: deque[Future[None]] = deque()
        self.cpr_support = CPR_Support.UNKNOWN
        if not output.responds_to_cpr:
            self.cpr_support = CPR_Support.NOT_SUPPORTED
        self._attrs_for_style: _StyleStringToAttrsCache | None = None
        self._style_string_has_style: _StyleStringHasStyleCache | None = None
        self._last_style_hash: Hashable | None = None
        self._last_transformation_hash: Hashable | None = None
        self._last_color_depth: ColorDepth | None = None
        self.reset(_scroll=True)

    @property
    def last_rendered_screen(self) ->(Screen | None):
        """
        The `Screen` class that was generated during the last rendering.
        This can be `None`.
        """
        pass

    @property
    def height_is_known(self) ->bool:
        """
        True when the height from the cursor until the bottom of the terminal
        is known. (It's often nicer to draw bottom toolbars only if the height
        is known, in order to avoid flickering when the CPR response arrives.)
        """
        pass

    @property
    def rows_above_layout(self) ->int:
        """
        Return the number of rows visible in the terminal above the layout.
        """
        pass

    def request_absolute_cursor_position(self) ->None:
        """
        Get current cursor position.

        We do this to calculate the minimum available height that we can
        consume for rendering the prompt. This is the available space below te
        cursor.

        For vt100: Do CPR request. (answer will arrive later.)
        For win32: Do API call. (Answer comes immediately.)
        """
        pass

    def report_absolute_cursor_row(self, row: int) ->None:
        """
        To be called when we know the absolute cursor position.
        (As an answer of a "Cursor Position Request" response.)
        """
        pass

    @property
    def waiting_for_cpr(self) ->bool:
        """
        Waiting for CPR flag. True when we send the request, but didn't got a
        response.
        """
        pass

    async def wait_for_cpr_responses(self, timeout: int=1) ->None:
        """
        Wait for a CPR response.
        """
        pass

    def render(self, app: Application[Any], layout: Layout, is_done: bool=False
        ) ->None:
        """
        Render the current interface to the output.

        :param is_done: When True, put the cursor at the end of the interface. We
                won't print any changes to this part.
        """
        pass

    def erase(self, leave_alternate_screen: bool=True) ->None:
        """
        Hide all output and put the cursor back at the first line. This is for
        instance used for running a system command (while hiding the CLI) and
        later resuming the same CLI.)

        :param leave_alternate_screen: When True, and when inside an alternate
            screen buffer, quit the alternate screen.
        """
        pass

    def clear(self) ->None:
        """
        Clear screen and go to 0,0
        """
        pass


def print_formatted_text(output: Output, formatted_text: AnyFormattedText,
    style: BaseStyle, style_transformation: (StyleTransformation | None)=
    None, color_depth: (ColorDepth | None)=None) ->None:
    """
    Print a list of (style_str, text) tuples in the given style to the output.
    """
    pass
