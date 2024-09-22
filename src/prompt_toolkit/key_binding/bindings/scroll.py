"""
Key bindings, for scrolling up and down through pages.

This are separate bindings, because GNU readline doesn't have them, but
they are very useful for navigating through long multiline buffers, like in
Vi, Emacs, etc...
"""
from __future__ import annotations
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
__all__ = ['scroll_forward', 'scroll_backward', 'scroll_half_page_up',
    'scroll_half_page_down', 'scroll_one_line_up', 'scroll_one_line_down']
E = KeyPressEvent


def scroll_forward(event: E, half: bool=False) ->None:
    """
    Scroll window down.
    """
    pass


def scroll_backward(event: E, half: bool=False) ->None:
    """
    Scroll window up.
    """
    pass


def scroll_half_page_down(event: E) ->None:
    """
    Same as ControlF, but only scroll half a page.
    """
    pass


def scroll_half_page_up(event: E) ->None:
    """
    Same as ControlB, but only scroll half a page.
    """
    pass


def scroll_one_line_down(event: E) ->None:
    """
    scroll_offset += 1
    """
    pass


def scroll_one_line_up(event: E) ->None:
    """
    scroll_offset -= 1
    """
    pass


def scroll_page_down(event: E) ->None:
    """
    Scroll page down. (Prefer the cursor at the top of the page, after scrolling.)
    """
    pass


def scroll_page_up(event: E) ->None:
    """
    Scroll page up. (Prefer the cursor at the bottom of the page, after scrolling.)
    """
    pass
