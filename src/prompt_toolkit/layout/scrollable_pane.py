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
        # Calculate dimensions
        xpos = write_position.xpos
        ypos = write_position.ypos
        width = write_position.width
        height = write_position.height

        # Create a temporary screen for rendering the full content
        temp_screen = Screen(self.max_available_height, width)
        temp_mouse_handlers = MouseHandlers()

        # Render content on the temporary screen
        self.content.write_to_screen(
            temp_screen,
            temp_mouse_handlers,
            WritePosition(xpos=0, ypos=0, width=width, height=self.max_available_height),
            parent_style,
            erase_bg,
            z_index
        )

        # Calculate the visible region
        visible_height = min(height, temp_screen.height - self.vertical_scroll)
        
        # Copy visible region to the actual screen
        self._copy_over_screen(screen, temp_screen, write_position, width)
        self._copy_over_mouse_handlers(mouse_handlers, temp_mouse_handlers, write_position, width)
        self._copy_over_write_positions(screen, temp_screen, write_position)

        # Draw scrollbar if needed
        if self.show_scrollbar() and temp_screen.height > height:
            self._draw_scrollbar(write_position, temp_screen.height, screen)

        # Make focused window visible if needed
        if self.keep_focused_window_visible():
            focused_windows = [
                w for w in temp_screen.visible_windows
                if w.render_info and w.render_info.get_visible_line_to_row_col
            ]
            if focused_windows:
                focused_window = focused_windows[-1]
                cursor_position = focused_window.render_info.cursor_position
                self._make_window_visible(visible_height, temp_screen.height,
                                          focused_window.render_info.window_write_position,
                                          cursor_position)

    def _clip_point_to_visible_area(self, point: Point, write_position:
        WritePosition) ->Point:
        """
        Ensure that the cursor and menu positions always are always reported
        within the visible area.
        """
        x = point.x
        y = point.y - self.vertical_scroll

        x = max(0, min(x, write_position.width - 1))
        y = max(0, min(y, write_position.height - 1))

        return Point(x=x, y=y)

    def _copy_over_screen(self, screen: Screen, temp_screen: Screen,
        write_position: WritePosition, virtual_width: int) ->None:
        """
        Copy over visible screen content and "zero width escape sequences".
        """
        for y in range(min(write_position.height, temp_screen.height - self.vertical_scroll)):
            for x in range(min(write_position.width, virtual_width)):
                temp_char = temp_screen.data_buffer[self.vertical_scroll + y][x]
                screen.data_buffer[write_position.ypos + y][write_position.xpos + x] = temp_char

        # Copy over zero width escape sequences
        for y in range(min(write_position.height, temp_screen.height - self.vertical_scroll)):
            row = self.vertical_scroll + y
            if row in temp_screen.zero_width_escapes:
                for x, escapes in temp_screen.zero_width_escapes[row].items():
                    if x < virtual_width:
                        screen.zero_width_escapes[write_position.ypos + y][write_position.xpos + x] = escapes

    def _copy_over_mouse_handlers(self, mouse_handlers: MouseHandlers,
        temp_mouse_handlers: MouseHandlers, write_position: WritePosition,
        virtual_width: int) ->None:
        """
        Copy over mouse handlers from virtual screen to real screen.

        Note: we take `virtual_width` because we don't want to copy over mouse
              handlers that we possibly have behind the scrollbar.
        """
        for y in range(min(write_position.height, self.max_available_height - self.vertical_scroll)):
            for x in range(min(write_position.width, virtual_width)):
                key = (self.vertical_scroll + y, x)
                if key in temp_mouse_handlers.mouse_handlers:
                    mouse_handlers.set_mouse_handler_for_region(
                        x=write_position.xpos + x,
                        y=write_position.ypos + y,
                        width=1,
                        height=1,
                        handler=temp_mouse_handlers.mouse_handlers[key]
                    )

    def _copy_over_write_positions(self, screen: Screen, temp_screen:
        Screen, write_position: WritePosition) ->None:
        """
        Copy over window write positions.
        """
        for window, positions in temp_screen.write_positions.items():
            new_positions = []
            for position in positions:
                new_ypos = position.ypos - self.vertical_scroll + write_position.ypos
                if write_position.ypos <= new_ypos < write_position.ypos + write_position.height:
                    new_positions.append(WritePosition(
                        xpos=position.xpos + write_position.xpos,
                        ypos=new_ypos,
                        width=min(position.width, write_position.width),
                        height=min(position.height, write_position.ypos + write_position.height - new_ypos)
                    ))
            if new_positions:
                screen.write_positions[window] = new_positions

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
        if cursor_position is not None:
            cursor_y = cursor_position.y
        else:
            cursor_y = visible_win_write_pos.ypos

        def scroll_to(scroll_offset):
            self.vertical_scroll = max(0, min(scroll_offset, virtual_height - visible_height))

        if self.keep_cursor_visible():
            # Scroll up if needed
            if cursor_y < self.vertical_scroll + self.scroll_offsets.top:
                scroll_to(cursor_y - self.scroll_offsets.top)

            # Scroll down if needed
            elif cursor_y >= self.vertical_scroll + visible_height - self.scroll_offsets.bottom:
                scroll_to(cursor_y - visible_height + 1 + self.scroll_offsets.bottom)

        else:
            # Scroll up if needed
            if visible_win_write_pos.ypos < self.vertical_scroll:
                scroll_to(visible_win_write_pos.ypos)

            # Scroll down if needed
            elif visible_win_write_pos.ypos + visible_win_write_pos.height > self.vertical_scroll + visible_height:
                scroll_to(visible_win_write_pos.ypos + visible_win_write_pos.height - visible_height)

    def _draw_scrollbar(self, write_position: WritePosition, content_height:
        int, screen: Screen) ->None:
        """
        Draw the scrollbar on the screen.

        Note: There is some code duplication with the `ScrollbarMargin`
              implementation.
        """
        window_height = write_position.height
        scrollbar_height = max(1, int(window_height * window_height / content_height))
        scrollbar_top = int(self.vertical_scroll * window_height / content_height)

        x = write_position.xpos + write_position.width - 1
        y = write_position.ypos

        # Draw scrollbar background
        for i in range(window_height):
            screen.data_buffer[y + i][x] = Char(' ', 'class:scrollbar.background')

        # Draw scrollbar itself
        for i in range(scrollbar_height):
            if 0 <= y + scrollbar_top + i < y + window_height:
                screen.data_buffer[y + scrollbar_top + i][x] = Char(' ', 'class:scrollbar')

        # Draw arrows
        if self.display_arrows():
            if self.vertical_scroll > 0:
                screen.data_buffer[y][x] = Char(self.up_arrow_symbol, 'class:scrollbar.arrow')
            if self.vertical_scroll + window_height < content_height:
                screen.data_buffer[y + window_height - 1][x] = Char(self.down_arrow_symbol, 'class:scrollbar.arrow')
