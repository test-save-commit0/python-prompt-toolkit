"""
Key bindings for extra page navigation: bindings for up/down scrolling through
long pages, like in Emacs or Vi.
"""
from __future__ import annotations
from prompt_toolkit.filters import buffer_has_focus, emacs_mode, vi_mode
from prompt_toolkit.key_binding.key_bindings import ConditionalKeyBindings, KeyBindings, KeyBindingsBase, merge_key_bindings
from .scroll import scroll_backward, scroll_forward, scroll_half_page_down, scroll_half_page_up, scroll_one_line_down, scroll_one_line_up, scroll_page_down, scroll_page_up
__all__ = ['load_page_navigation_bindings',
    'load_emacs_page_navigation_bindings', 'load_vi_page_navigation_bindings']


def load_page_navigation_bindings() ->KeyBindingsBase:
    """
    Load both the Vi and Emacs bindings for page navigation.
    """
    pass


def load_emacs_page_navigation_bindings() ->KeyBindingsBase:
    """
    Key bindings, for scrolling up and down through pages.
    This are separate bindings, because GNU readline doesn't have them.
    """
    pass


def load_vi_page_navigation_bindings() ->KeyBindingsBase:
    """
    Key bindings, for scrolling up and down through pages.
    This are separate bindings, because GNU readline doesn't have them.
    """
    pass
