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
    width = size.columns

    # Create locals for faster access
    write = output.write
    write_position = output.set_cursor_position
    move_cursor = output.move_cursor

    # Skip first empty lines. (This is a performance optimization.)
    if previous_screen is None:
        row = 0
    else:
        row = 0
        while row < screen.height and row < previous_screen.height and screen.data_buffer[row] == previous_screen.data_buffer[row]:
            row += 1

    # Render output
    for y in range(row, screen.height):
        row = screen.data_buffer[y]
        previous_row = previous_screen.data_buffer[y] if previous_screen and y < previous_screen.height else None

        col = 0
        while col < width:
            char = row[col]
            char_width = char.width or 1

            if previous_row:
                previous_char = previous_row[col]
                if char == previous_char:
                    col += char_width
                    continue

            current_pos = Point(x=col, y=y)
            write_position(current_pos.x, current_pos.y)
            style = char.style

            if style != last_style:
                attrs = attrs_for_style_string[style]
                output.set_attributes(attrs, color_depth)
                last_style = style

            write(char.char)
            col += char_width

    # Move cursor
    if is_done:
        write_position(screen.cursor_position.x, screen.cursor_position.y)
    else:
        move_cursor(screen.cursor_position.x - current_pos.x, screen.cursor_position.y - current_pos.y)

    return screen.cursor_position, last_style


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
        return getattr(self, '_last_rendered_screen', None)

    @property
    def height_is_known(self) ->bool:
        """
        True when the height from the cursor until the bottom of the terminal
        is known. (It's often nicer to draw bottom toolbars only if the height
        is known, in order to avoid flickering when the CPR response arrives.)
        """
        return self.cpr_support != CPR_Support.UNKNOWN and not self.waiting_for_cpr

    @property
    def rows_above_layout(self) ->int:
        """
        Return the number of rows visible in the terminal above the layout.
        """
        if self.cpr_support == CPR_Support.SUPPORTED:
            return self._rows_above_layout
        else:
            return 0

    def request_absolute_cursor_position(self) ->None:
        """
        Get current cursor position.

        We do this to calculate the minimum available height that we can
        consume for rendering the prompt. This is the available space below te
        cursor.

        For vt100: Do CPR request. (answer will arrive later.)
        For win32: Do API call. (Answer comes immediately.)
        """
        if self.cpr_support != CPR_Support.NOT_SUPPORTED:
            self.output.get_cursor_position()
            self.cpr_support = CPR_Support.SUPPORTED

        if self.cpr_support == CPR_Support.NOT_SUPPORTED:
            if self.cpr_not_supported_callback:
                self.cpr_not_supported_callback()

    def report_absolute_cursor_row(self, row: int) ->None:
        """
        To be called when we know the absolute cursor position.
        (As an answer of a "Cursor Position Request" response.)
        """
        self._rows_above_layout = row - 1

        # Resolve future.
        if self._waiting_for_cpr_futures:
            for f in self._waiting_for_cpr_futures:
                f.set_result(None)
            self._waiting_for_cpr_futures = deque()

    @property
    def waiting_for_cpr(self) ->bool:
        """
        Waiting for CPR flag. True when we send the request, but didn't got a
        response.
        """
        return bool(self._waiting_for_cpr_futures)

    async def wait_for_cpr_responses(self, timeout: int=1) ->None:
        """
        Wait for a CPR response.
        """
        if self._waiting_for_cpr_futures:
            await wait(list(self._waiting_for_cpr_futures), timeout=timeout)

    def render(self, app: Application[Any], layout: Layout, is_done: bool=False
        ) ->None:
        """
        Render the current interface to the output.

        :param is_done: When True, put the cursor at the end of the interface. We
                won't print any changes to this part.
        """
        output = self.output
        screen = layout.screen

        if is_done:
            self.request_absolute_cursor_position()

        # Enter alternate screen.
        if self.full_screen and not self._in_alternate_screen:
            self._in_alternate_screen = True
            output.enter_alternate_screen()

        # Enable/disable mouse support.
        needs_mouse_support = self.mouse_support()
        if needs_mouse_support != self._mouse_support_enabled:
            if needs_mouse_support:
                output.enable_mouse_support()
            else:
                output.disable_mouse_support()
            self._mouse_support_enabled = needs_mouse_support

        # Enable bracketed paste.
        if not self._bracketed_paste_enabled:
            output.enable_bracketed_paste()
            self._bracketed_paste_enabled = True

        # Reset cursor key mode.
        if not self._cursor_key_mode_reset:
            output.reset_cursor_key_mode()
            self._cursor_key_mode_reset = True

        # Create new style transformation.
        style_transformation = app.style_transformation or DummyStyleTransformation()

        # Create new Cache objects.
        style_hash = hash((app.style, style_transformation))
        color_depth = output.get_default_color_depth()

        if (style_hash != self._last_style_hash or
            color_depth != self._last_color_depth):
            self._attrs_for_style = _StyleStringToAttrsCache(
                get_attrs_for_style_str=lambda style_str: app.style.get_attrs_for_style_str(style_str),
                style_transformation=style_transformation)
            self._style_string_has_style = _StyleStringHasStyleCache(self._attrs_for_style)

        self._last_style_hash = style_hash
        self._last_color_depth = color_depth

        # Render to screen.
        size = output.get_size()
        if self.full_screen:
            screen.resize(size)
        else:
            screen.resize(Size(rows=size.rows, columns=size.columns))

        # Calculate the difference between this and the previous screen.
        current_pos, last_style = _output_screen_diff(
            app,
            output,
            screen,
            current_pos=Point(0, 0),
            color_depth=color_depth,
            previous_screen=self._last_rendered_screen,
            last_style=None,
            is_done=is_done,
            full_screen=self.full_screen,
            attrs_for_style_string=self._attrs_for_style,
            style_string_has_style=self._style_string_has_style,
            size=size,
            previous_width=(self._last_rendered_screen.width
                            if self._last_rendered_screen else 0))

        output.flush()
        self._last_rendered_screen = screen

    def erase(self, leave_alternate_screen: bool=True) ->None:
        """
        Hide all output and put the cursor back at the first line. This is for
        instance used for running a system command (while hiding the CLI) and
        later resuming the same CLI.)

        :param leave_alternate_screen: When True, and when inside an alternate
            screen buffer, quit the alternate screen.
        """
        output = self.output

        output.erase_screen()
        output.reset_attributes()
        output.disable_mouse_support()
        output.disable_bracketed_paste()
        output.reset_cursor_key_mode()

        if leave_alternate_screen and self._in_alternate_screen:
            output.quit_alternate_screen()
            self._in_alternate_screen = False

        self._last_rendered_screen = None
        output.flush()

    def clear(self) ->None:
        """
        Clear screen and go to 0,0
        """
        output = self.output

        output.erase_screen()
        output.cursor_goto(0, 0)
        output.flush()


def print_formatted_text(output: Output, formatted_text: AnyFormattedText,
    style: BaseStyle, style_transformation: (StyleTransformation | None)=
    None, color_depth: (ColorDepth | None)=None) ->None:
    """
    Print a list of (style_str, text) tuples in the given style to the output.
    """
    pass
