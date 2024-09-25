from __future__ import annotations
import math
from itertools import zip_longest
from typing import TYPE_CHECKING, Callable, Iterable, Sequence, TypeVar, cast
from weakref import WeakKeyDictionary
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import CompletionState
from prompt_toolkit.completion import Completion
from prompt_toolkit.data_structures import Point
from prompt_toolkit.filters import Condition, FilterOrBool, has_completions, is_done, to_filter
from prompt_toolkit.formatted_text import StyleAndTextTuples, fragment_list_width, to_formatted_text
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.utils import get_cwidth
from .containers import ConditionalContainer, HSplit, ScrollOffsets, Window
from .controls import GetLinePrefixCallable, UIContent, UIControl
from .dimension import Dimension
from .margins import ScrollbarMargin
if TYPE_CHECKING:
    from prompt_toolkit.key_binding.key_bindings import KeyBindings, NotImplementedOrNone
__all__ = ['CompletionsMenu', 'MultiColumnCompletionsMenu']
E = KeyPressEvent


class CompletionsMenuControl(UIControl):
    """
    Helper for drawing the complete menu to the screen.

    :param scroll_offset: Number (integer) representing the preferred amount of
        completions to be displayed before and after the current one. When this
        is a very high number, the current completion will be shown in the
        middle most of the time.
    """
    MIN_WIDTH = 7

    def create_content(self, width: int, height: int) ->UIContent:
        """
        Create a UIContent object for this control.
        """
        complete_state = get_app().current_buffer.complete_state
        if complete_state is None:
            return UIContent()

        completions = complete_state.completions
        index = complete_state.complete_index  # Can be None!

        # Calculate width of completions menu.
        menu_width = self._get_menu_width(width, complete_state)
        menu_meta_width = self._get_menu_meta_width(width, complete_state)
        show_meta = self._show_meta(complete_state)

        def get_line(i):
            c = completions[i]
            is_current_completion = (i == index)
            result = _get_menu_item_fragments(c, is_current_completion, menu_width, space_after=show_meta)

            if show_meta:
                result += _get_menu_item_fragments(c.display_meta, is_current_completion, menu_meta_width)

            return result

        return UIContent(get_line=get_line,
                         cursor_position=Point(x=0, y=index or 0),
                         line_count=len(completions))

    def _show_meta(self, complete_state: CompletionState) ->bool:
        """
        Return ``True`` if we need to show a column with meta information.
        """
        return any(c.display_meta for c in complete_state.completions)

    def _get_menu_width(self, max_width: int, complete_state: CompletionState
        ) ->int:
        """
        Return the width of the main column.
        """
        return min(max_width, max(self.MIN_WIDTH, max(get_cwidth(c.display) for c in complete_state.completions) + 2))

    def _get_menu_meta_width(self, max_width: int, complete_state:
        CompletionState) ->int:
        """
        Return the width of the meta column.
        """
        if self._show_meta(complete_state):
            return min(max_width // 2, max(get_cwidth(c.display_meta) for c in complete_state.completions if c.display_meta))
        return 0

    def mouse_handler(self, mouse_event: MouseEvent) ->NotImplementedOrNone:
        """
        Handle mouse events: clicking and scrolling.
        """
        b = get_app().current_buffer
        complete_state = b.complete_state

        if complete_state is None:
            return NotImplemented

        # Mouse click
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            index = mouse_event.position.y

            if 0 <= index < len(complete_state.completions):
                b.apply_completion(complete_state.completions[index])
                return None

        # Scroll up/down
        if mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            b.complete_next()
            return None
        elif mouse_event.event_type == MouseEventType.SCROLL_UP:
            b.complete_previous()
            return None

        return NotImplemented


def _get_menu_item_fragments(completion: Completion, is_current_completion:
    bool, width: int, space_after: bool=False) ->StyleAndTextTuples:
    """
    Get the style/text tuples for a menu item, styled and trimmed to the given
    width.
    """
    style = 'class:completion-menu.completion'
    if is_current_completion:
        style += '.current'

    text = completion.display
    text, text_width = _trim_formatted_text([(style, text)], width)

    padding = width - text_width
    if space_after:
        padding -= 1

    if padding > 0:
        text.append((style, ' ' * padding))

    if space_after:
        text.append((style, ' '))

    return text


def _trim_formatted_text(formatted_text: StyleAndTextTuples, max_width: int
    ) ->tuple[StyleAndTextTuples, int]:
    """
    Trim the text to `max_width`, append dots when the text is too long.
    Returns (text, width) tuple.
    """
    result: StyleAndTextTuples = []
    current_width = 0

    for style, text in formatted_text:
        for c in text:
            char_width = get_cwidth(c)
            if current_width + char_width > max_width:
                result.append((style, '...'))
                current_width += 3
                return result, current_width

            result.append((style, c))
            current_width += char_width

    return result, current_width


class CompletionsMenu(ConditionalContainer):

    def __init__(self, max_height: (int | None)=None, scroll_offset: (int |
        Callable[[], int])=0, extra_filter: FilterOrBool=True,
        display_arrows: FilterOrBool=False, z_index: int=10 ** 8) ->None:
        extra_filter = to_filter(extra_filter)
        display_arrows = to_filter(display_arrows)
        super().__init__(content=Window(content=CompletionsMenuControl(),
            width=Dimension(min=8), height=Dimension(min=1, max=max_height),
            scroll_offsets=ScrollOffsets(top=scroll_offset, bottom=
            scroll_offset), right_margins=[ScrollbarMargin(display_arrows=
            display_arrows)], dont_extend_width=True, style=
            'class:completion-menu', z_index=z_index), filter=extra_filter &
            has_completions & ~is_done)


class MultiColumnCompletionMenuControl(UIControl):
    """
    Completion menu that displays all the completions in several columns.
    When there are more completions than space for them to be displayed, an
    arrow is shown on the left or right side.

    `min_rows` indicates how many rows will be available in any possible case.
    When this is larger than one, it will try to use less columns and more
    rows until this value is reached.
    Be careful passing in a too big value, if less than the given amount of
    rows are available, more columns would have been required, but
    `preferred_width` doesn't know about that and reports a too small value.
    This results in less completions displayed and additional scrolling.
    (It's a limitation of how the layout engine currently works: first the
    widths are calculated, then the heights.)

    :param suggested_max_column_width: The suggested max width of a column.
        The column can still be bigger than this, but if there is place for two
        columns of this width, we will display two columns. This to avoid that
        if there is one very wide completion, that it doesn't significantly
        reduce the amount of columns.
    """
    _required_margin = 3

    def __init__(self, min_rows: int=3, suggested_max_column_width: int=30
        ) ->None:
        assert min_rows >= 1
        self.min_rows = min_rows
        self.suggested_max_column_width = suggested_max_column_width
        self.scroll = 0
        self._column_width_for_completion_state: WeakKeyDictionary[
            CompletionState, tuple[int, int]] = WeakKeyDictionary()
        self._rendered_rows = 0
        self._rendered_columns = 0
        self._total_columns = 0
        self._render_pos_to_completion: dict[tuple[int, int], Completion] = {}
        self._render_left_arrow = False
        self._render_right_arrow = False
        self._render_width = 0

    def preferred_width(self, max_available_width: int) ->(int | None):
        """
        Preferred width: prefer to use at least min_rows, but otherwise as much
        as possible horizontally.
        """
        complete_state = get_app().current_buffer.complete_state
        if complete_state is None:
            return 0

        column_width = self._get_column_width(complete_state)
        max_columns = max(1, (max_available_width - self._required_margin) // column_width)

        return min(
            max_available_width,
            max(
                self._required_margin + column_width,
                column_width * max_columns + self._required_margin
            )
        )

    def preferred_height(self, width: int, max_available_height: int,
        wrap_lines: bool, get_line_prefix: (GetLinePrefixCallable | None)) ->(
        int | None):
        """
        Preferred height: as much as needed in order to display all the completions.
        """
        complete_state = get_app().current_buffer.complete_state
        if complete_state is None:
            return 0

        column_width = self._get_column_width(complete_state)
        column_count = max(1, (width - self._required_margin) // column_width)
        row_count = int(math.ceil(len(complete_state.completions) / float(column_count)))
        return max(self.min_rows, min(row_count, max_available_height))

    def create_content(self, width: int, height: int) ->UIContent:
        """
        Create a UIContent object for this menu.
        """
        complete_state = get_app().current_buffer.complete_state
        if complete_state is None:
            return UIContent()

        column_width = self._get_column_width(complete_state)
        self._render_pos_to_completion = {}
        self._render_left_arrow = False
        self._render_right_arrow = False
        self._render_width = width

        visible_columns = max(1, (width - self._required_margin) // column_width)
        visible_rows = height

        columns = []
        for i in range(visible_columns):
            col_start = i * visible_rows - self.scroll
            col_end = (i + 1) * visible_rows - self.scroll
            columns.append(complete_state.completions[col_start:col_end])

        def get_line(y):
            result = []
            for x, column in enumerate(columns):
                if y < len(column):
                    completion = column[y]
                    style = 'class:completion-menu.completion'
                    if complete_state.complete_index == self.scroll + x * visible_rows + y:
                        style += '.current'
                    result.extend(_get_menu_item_fragments(completion, False, column_width - 1, True))
                    self._render_pos_to_completion[x, y] = completion
                else:
                    result.append(('', ' ' * column_width))
            return result

        self._rendered_rows = visible_rows
        self._rendered_columns = visible_columns
        self._total_columns = int(math.ceil(len(complete_state.completions) / float(visible_rows)))

        # Show left/right arrows (for scrolling) if there are more completions than visible.
        if self.scroll > 0:
            self._render_left_arrow = True
        if self.scroll < (self._total_columns - visible_columns) * visible_rows:
            self._render_right_arrow = True

        return UIContent(get_line=get_line,
                         line_count=visible_rows,
                         show_cursor=False)

    def _get_column_width(self, completion_state: CompletionState) ->int:
        """
        Return the width of each column.
        """
        if completion_state in self._column_width_for_completion_state:
            return self._column_width_for_completion_state[completion_state][0]

        max_width = max(get_cwidth(c.display) for c in completion_state.completions)
        result = max(self.suggested_max_column_width, max_width)
        self._column_width_for_completion_state[completion_state] = (result, max_width)
        return result

    def mouse_handler(self, mouse_event: MouseEvent) ->NotImplementedOrNone:
        """
        Handle scroll and click events.
        """
        if mouse_event.event_type == MouseEventType.SCROLL_DOWN:
            self.scroll += self._rendered_rows
            self.scroll = min(self.scroll, (self._total_columns - self._rendered_columns) * self._rendered_rows)
        elif mouse_event.event_type == MouseEventType.SCROLL_UP:
            self.scroll -= self._rendered_rows
            self.scroll = max(0, self.scroll)
        elif mouse_event.event_type == MouseEventType.MOUSE_UP:
            x = mouse_event.position.x
            y = mouse_event.position.y

            if x == 0 and self._render_left_arrow:
                self.scroll -= self._rendered_rows
                self.scroll = max(0, self.scroll)
            elif x == self._render_width - 1 and self._render_right_arrow:
                self.scroll += self._rendered_rows
                self.scroll = min(self.scroll, (self._total_columns - self._rendered_columns) * self._rendered_rows)
            elif (x, y) in self._render_pos_to_completion:
                completion = self._render_pos_to_completion[x, y]
                get_app().current_buffer.apply_completion(completion)

        return None

    def get_key_bindings(self) ->KeyBindings:
        """
        Expose key bindings that handle the left/right arrow keys when the menu
        is displayed.
        """
        kb = KeyBindings()

        @kb.add('left', filter=~has_completions)
        def _(event):
            self.scroll -= self._rendered_rows
            self.scroll = max(0, self.scroll)

        @kb.add('right', filter=~has_completions)
        def _(event):
            self.scroll += self._rendered_rows
            self.scroll = min(self.scroll, (self._total_columns - self._rendered_columns) * self._rendered_rows)

        return kb


class MultiColumnCompletionsMenu(HSplit):
    """
    Container that displays the completions in several columns.
    When `show_meta` (a :class:`~prompt_toolkit.filters.Filter`) evaluates
    to True, it shows the meta information at the bottom.
    """

    def __init__(self, min_rows: int=3, suggested_max_column_width: int=30,
        show_meta: FilterOrBool=True, extra_filter: FilterOrBool=True,
        z_index: int=10 ** 8) ->None:
        show_meta = to_filter(show_meta)
        extra_filter = to_filter(extra_filter)
        full_filter = extra_filter & has_completions & ~is_done

        @Condition
        def any_completion_has_meta() ->bool:
            complete_state = get_app().current_buffer.complete_state
            return complete_state is not None and any(c.display_meta for c in
                complete_state.completions)
        completions_window = ConditionalContainer(content=Window(content=
            MultiColumnCompletionMenuControl(min_rows=min_rows,
            suggested_max_column_width=suggested_max_column_width), width=
            Dimension(min=8), height=Dimension(min=1)), filter=full_filter)
        meta_window = ConditionalContainer(content=Window(content=
            _SelectedCompletionMetaControl()), filter=full_filter &
            show_meta & any_completion_has_meta)
        super().__init__([completions_window, meta_window], z_index=z_index)


class _SelectedCompletionMetaControl(UIControl):
    """
    Control that shows the meta information of the selected completion.
    """

    def preferred_width(self, max_available_width: int) ->(int | None):
        """
        Report the width of the longest meta text as the preferred width of this control.

        It could be that we use less width, but this way, we're sure that the
        layout doesn't change when we select another completion (E.g. that
        completions are suddenly shown in more or fewer columns.)
        """
        complete_state = get_app().current_buffer.complete_state
        if complete_state is None:
            return None

        max_meta_width = max(get_cwidth(c.display_meta) for c in complete_state.completions if c.display_meta)
        return min(max_meta_width, max_available_width)
