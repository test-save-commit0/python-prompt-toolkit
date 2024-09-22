from __future__ import annotations
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import FilterOrBool, to_filter
from prompt_toolkit.key_binding import KeyBindingsBase
from prompt_toolkit.mouse_events import MouseEvent
from .containers import Container, ScrollOffsets
from .dimension import AnyDimension, Dimension, sum_layout_dimensions, to_dimension
from .mouse_handlers import MouseHandler, MouseHandlers
from .screen import Char, Screen, WritePosition
__all__ = ['ScrollablePane']
MAX_AVAILABLE_HEIGHT = 10000


class ScrollablePane(Container):
    """
    Container widget that exposes a larger virtual screen to its content and
    displays it in a vertical scrollbale region.

    Typically this is wrapped in a large `HSplit` container. Make sure in that
    case to not specify a `height` dimension of the `HSplit`, so that it will
    scale according to the content.

    .. note::

        If you want to display a completion menu for widgets in this
        `ScrollablePane`, then it's still a good practice to use a
        `FloatContainer` with a `CompletionsMenu` in a `Float` at the top-level
        of the layout hierarchy, rather then nesting a `FloatContainer` in this
        `ScrollablePane`. (Otherwise, it's possible that the completion menu
        is clipped.)

    :param content: The content container.
    :param scrolloffset: Try to keep the cursor within this distance from the
        top/bottom (left/right offset is not used).
    :param keep_cursor_visible: When `True`, automatically scroll the pane so
        that the cursor (of the focused window) is always visible.
    :param keep_focused_window_visible: When `True`, automatically scroll the
        pane so that the focused window is visible, or as much visible as
        possible if it doesn't completely fit the screen.
    :param max_available_height: Always constraint the height to this amount
        for performance reasons.
    :param width: When given, use this width instead of looking at the children.
    :param height: When given, use this height instead of looking at the children.
    :param show_scrollbar: When `True` display a scrollbar on the right.
    """

    def __init__(self, content: Container, scroll_offsets: (ScrollOffsets |
        None)=None, keep_cursor_visible: FilterOrBool=True,
        keep_focused_window_visible: FilterOrBool=True,
        max_available_height: int=MAX_AVAILABLE_HEIGHT, width: AnyDimension
        =None, height: AnyDimension=None, show_scrollbar: FilterOrBool=True,
        display_arrows: FilterOrBool=True, up_arrow_symbol: str='^',
        down_arrow_symbol: str='v') ->None:
        self.content = content
        self.scroll_offsets = scroll_offsets or ScrollOffsets(top=1, bottom=1)
        self.keep_cursor_visible = to_filter(keep_cursor_visible)
        self.keep_focused_window_visible = to_filter(
            keep_focused_window_visible)
        self.max_available_height = max_available_height
        self.width = width
        self.height = height
        self.show_scrollbar = to_filter(show_scrollbar)
        self.display_arrows = to_filter(display_arrows)
        self.up_arrow_symbol = up_arrow_symbol
        self.down_arrow_symbol = down_arrow_symbol
        self.vertical_scroll = 0

    def __repr__(self) ->str:
        return f'ScrollablePane({self.content!r})'

    def write_to_screen(self, screen: Screen, mouse_handlers: MouseHandlers,
        write_position: WritePosition, parent_style: str, erase_bg: bool,
        z_index: (int | None)) ->None:
        """
        Render scrollable pane content.

        This works by rendering on an off-screen canvas, and copying over the
        visible region.
        """
        pass

    def _clip_point_to_visible_area(self, point: Point, write_position:
        WritePosition) ->Point:
        """
        Ensure that the cursor and menu positions always are always reported
        """
        pass

    def _copy_over_screen(self, screen: Screen, temp_screen: Screen,
        write_position: WritePosition, virtual_width: int) ->None:
        """
        Copy over visible screen content and "zero width escape sequences".
        """
        pass

    def _copy_over_mouse_handlers(self, mouse_handlers: MouseHandlers,
        temp_mouse_handlers: MouseHandlers, write_position: WritePosition,
        virtual_width: int) ->None:
        """
        Copy over mouse handlers from virtual screen to real screen.

        Note: we take `virtual_width` because we don't want to copy over mouse
              handlers that we possibly have behind the scrollbar.
        """
        pass

    def _copy_over_write_positions(self, screen: Screen, temp_screen:
        Screen, write_position: WritePosition) ->None:
        """
        Copy over window write positions.
        """
        pass

    def _make_window_visible(self, visible_height: int, virtual_height: int,
        visible_win_write_pos: WritePosition, cursor_position: (Point | None)
        ) ->None:
        """
        Scroll the scrollable pane, so that this window becomes visible.

        :param visible_height: Height of this `ScrollablePane` that is rendered.
        :param virtual_height: Height of the virtual, temp screen.
        :param visible_win_write_pos: `WritePosition` of the nested window on the
            temp screen.
        :param cursor_position: The location of the cursor position of this
            window on the temp screen.
        """
        pass

    def _draw_scrollbar(self, write_position: WritePosition, content_height:
        int, screen: Screen) ->None:
        """
        Draw the scrollbar on the screen.

        Note: There is some code duplication with the `ScrollbarMargin`
              implementation.
        """
        pass
