"""
Filters that accept a `Application` as argument.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, cast
from prompt_toolkit.application.current import get_app
from prompt_toolkit.cache import memoized
from prompt_toolkit.enums import EditingMode
from .base import Condition
if TYPE_CHECKING:
    from prompt_toolkit.layout.layout import FocusableElement
__all__ = ['has_arg', 'has_completions', 'completion_is_selected',
    'has_focus', 'buffer_has_focus', 'has_selection', 'has_suggestion',
    'has_validation_error', 'is_done', 'is_read_only', 'is_multiline',
    'renderer_height_is_known', 'in_editing_mode', 'in_paste_mode',
    'vi_mode', 'vi_navigation_mode', 'vi_insert_mode',
    'vi_insert_multiple_mode', 'vi_replace_mode', 'vi_selection_mode',
    'vi_waiting_for_text_object_mode', 'vi_digraph_mode',
    'vi_recording_macro', 'emacs_mode', 'emacs_insert_mode',
    'emacs_selection_mode', 'shift_selection_mode', 'is_searching',
    'control_is_searchable', 'vi_search_direction_reversed']


def has_focus(value: FocusableElement) ->Condition:
    """
    Enable when this buffer has the focus.
    """
    pass


@Condition
def buffer_has_focus() ->bool:
    """
    Enabled when the currently focused control is a `BufferControl`.
    """
    pass


@Condition
def has_selection() ->bool:
    """
    Enable when the current buffer has a selection.
    """
    pass


@Condition
def has_suggestion() ->bool:
    """
    Enable when the current buffer has a suggestion.
    """
    pass


@Condition
def has_completions() ->bool:
    """
    Enable when the current buffer has completions.
    """
    pass


@Condition
def completion_is_selected() ->bool:
    """
    True when the user selected a completion.
    """
    pass


@Condition
def is_read_only() ->bool:
    """
    True when the current buffer is read only.
    """
    pass


@Condition
def is_multiline() ->bool:
    """
    True when the current buffer has been marked as multiline.
    """
    pass


@Condition
def has_validation_error() ->bool:
    """Current buffer has validation error."""
    pass


@Condition
def has_arg() ->bool:
    """Enable when the input processor has an 'arg'."""
    pass


@Condition
def is_done() ->bool:
    """
    True when the CLI is returning, aborting or exiting.
    """
    pass


@Condition
def renderer_height_is_known() ->bool:
    """
    Only True when the renderer knows it's real height.

    (On VT100 terminals, we have to wait for a CPR response, before we can be
    sure of the available height between the cursor position and the bottom of
    the terminal. And usually it's nicer to wait with drawing bottom toolbars
    until we receive the height, in order to avoid flickering -- first drawing
    somewhere in the middle, and then again at the bottom.)
    """
    pass


@memoized()
def in_editing_mode(editing_mode: EditingMode) ->Condition:
    """
    Check whether a given editing mode is active. (Vi or Emacs.)
    """
    pass


@Condition
def vi_navigation_mode() ->bool:
    """
    Active when the set for Vi navigation key bindings are active.
    """
    pass


@Condition
def vi_recording_macro() ->bool:
    """When recording a Vi macro."""
    pass


@Condition
def emacs_mode() ->bool:
    """When the Emacs bindings are active."""
    pass


@Condition
def is_searching() ->bool:
    """When we are searching."""
    pass


@Condition
def control_is_searchable() ->bool:
    """When the current UIControl is searchable."""
    pass


@Condition
def vi_search_direction_reversed() ->bool:
    """When the '/' and '?' key bindings for Vi-style searching have been reversed."""
    pass
