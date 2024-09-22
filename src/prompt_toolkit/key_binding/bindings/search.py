"""
Search related key bindings.
"""
from __future__ import annotations
from prompt_toolkit import search
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition, control_is_searchable, is_searching
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from ..key_bindings import key_binding
__all__ = ['abort_search', 'accept_search',
    'start_reverse_incremental_search', 'start_forward_incremental_search',
    'reverse_incremental_search', 'forward_incremental_search',
    'accept_search_and_accept_input']
E = KeyPressEvent


@key_binding(filter=is_searching)
def abort_search(event: E) ->None:
    """
    Abort an incremental search and restore the original
    line.
    (Usually bound to ControlG/ControlC.)
    """
    pass


@key_binding(filter=is_searching)
def accept_search(event: E) ->None:
    """
    When enter pressed in isearch, quit isearch mode. (Multiline
    isearch would be too complicated.)
    (Usually bound to Enter.)
    """
    pass


@key_binding(filter=control_is_searchable)
def start_reverse_incremental_search(event: E) ->None:
    """
    Enter reverse incremental search.
    (Usually ControlR.)
    """
    pass


@key_binding(filter=control_is_searchable)
def start_forward_incremental_search(event: E) ->None:
    """
    Enter forward incremental search.
    (Usually ControlS.)
    """
    pass


@key_binding(filter=is_searching)
def reverse_incremental_search(event: E) ->None:
    """
    Apply reverse incremental search, but keep search buffer focused.
    """
    pass


@key_binding(filter=is_searching)
def forward_incremental_search(event: E) ->None:
    """
    Apply forward incremental search, but keep search buffer focused.
    """
    pass


@Condition
def _previous_buffer_is_returnable() ->bool:
    """
    True if the previously focused buffer has a return handler.
    """
    pass


@key_binding(filter=is_searching & _previous_buffer_is_returnable)
def accept_search_and_accept_input(event: E) ->None:
    """
    Accept the search operation first, then accept the input.
    """
    pass
