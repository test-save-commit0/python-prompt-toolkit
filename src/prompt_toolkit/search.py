"""
Search operations.

For the key bindings implementation with attached filters, check
`prompt_toolkit.key_binding.bindings.search`. (Use these for new key bindings
instead of calling these function directly.)
"""
from __future__ import annotations
from enum import Enum
from typing import TYPE_CHECKING
from .application.current import get_app
from .filters import FilterOrBool, is_searching, to_filter
from .key_binding.vi_state import InputMode
if TYPE_CHECKING:
    from prompt_toolkit.layout.controls import BufferControl, SearchBufferControl
    from prompt_toolkit.layout.layout import Layout
__all__ = ['SearchDirection', 'start_search', 'stop_search']


class SearchDirection(Enum):
    FORWARD = 'FORWARD'
    BACKWARD = 'BACKWARD'


class SearchState:
    """
    A search 'query', associated with a search field (like a SearchToolbar).

    Every searchable `BufferControl` points to a `search_buffer_control`
    (another `BufferControls`) which represents the search field. The
    `SearchState` attached to that search field is used for storing the current
    search query.

    It is possible to have one searchfield for multiple `BufferControls`. In
    that case, they'll share the same `SearchState`.
    If there are multiple `BufferControls` that display the same `Buffer`, then
    they can have a different `SearchState` each (if they have a different
    search control).
    """
    __slots__ = 'text', 'direction', 'ignore_case'

    def __init__(self, text: str='', direction: SearchDirection=
        SearchDirection.FORWARD, ignore_case: FilterOrBool=False) ->None:
        self.text = text
        self.direction = direction
        self.ignore_case = to_filter(ignore_case)

    def __repr__(self) ->str:
        return '{}({!r}, direction={!r}, ignore_case={!r})'.format(self.
            __class__.__name__, self.text, self.direction, self.ignore_case)

    def __invert__(self) ->SearchState:
        """
        Create a new SearchState where backwards becomes forwards and the other
        way around.
        """
        if self.direction == SearchDirection.BACKWARD:
            direction = SearchDirection.FORWARD
        else:
            direction = SearchDirection.BACKWARD
        return SearchState(text=self.text, direction=direction, ignore_case
            =self.ignore_case)


def start_search(buffer_control: (BufferControl | None)=None, direction:
    SearchDirection=SearchDirection.FORWARD) ->None:
    """
    Start search through the given `buffer_control` using the
    `search_buffer_control`.

    :param buffer_control: Start search for this `BufferControl`. If not given,
        search through the current control.
    """
    app = get_app()
    
    if buffer_control is None:
        buffer_control = app.layout.current_control

    search_control = _get_reverse_search_links(app.layout).get(buffer_control)
    
    if search_control:
        buffer_control.search_state = SearchState(direction=direction)
        app.layout.focus(search_control)
        search_control.buffer.reset()


def stop_search(buffer_control: (BufferControl | None)=None) ->None:
    """
    Stop search through the given `buffer_control`.
    """
    app = get_app()
    
    if buffer_control is None:
        buffer_control = app.layout.current_control

    if buffer_control.search_state:
        buffer_control.search_state = None
        app.layout.focus(buffer_control)


def do_incremental_search(direction: SearchDirection, count: int=1) ->None:
    """
    Apply search, but keep search buffer focused.
    """
    app = get_app()
    search_control = app.layout.current_control

    if isinstance(search_control, SearchBufferControl):
        buffer_control = search_control.buffer_control
        if buffer_control and buffer_control.search_state:
            buffer_control.search_state.direction = direction
            
            for _ in range(count):
                buffer_control.search(buffer_control.search_state.text,
                                      direction,
                                      count=1,
                                      include_current_position=False)


def accept_search() ->None:
    """
    Accept current search query. Focus original `BufferControl` again.
    """
    app = get_app()
    search_control = app.layout.current_control

    if isinstance(search_control, SearchBufferControl):
        buffer_control = search_control.buffer_control
        if buffer_control:
            app.layout.focus(buffer_control)

            # If we're in Vi mode and in navigation mode, go back to 
            # insert mode.
            if app.vi_state.input_mode == InputMode.NAVIGATION:
                app.vi_state.input_mode = InputMode.INSERT


def _get_reverse_search_links(layout: Layout) ->dict[BufferControl,
    SearchBufferControl]:
    """
    Return mapping from BufferControl to SearchBufferControl.
    """
    result = {}
    for search_control in layout.find_all_controls(lambda c: isinstance(c, SearchBufferControl)):
        if search_control.buffer_control:
            result[search_control.buffer_control] = search_control
    return result
