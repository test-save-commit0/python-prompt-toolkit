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
    return merge_key_bindings([
        load_emacs_page_navigation_bindings(),
        load_vi_page_navigation_bindings()
    ])


def load_emacs_page_navigation_bindings() ->KeyBindingsBase:
    """
    Key bindings, for scrolling up and down through pages.
    This are separate bindings, because GNU readline doesn't have them.
    """
    kb = KeyBindings()

    @kb.add('c-v')
    def _(event):
        " Scroll half page down. "
        scroll_half_page_down(event)

    @kb.add('pagedown')
    def _(event):
        " Scroll one page down. "
        scroll_page_down(event)

    @kb.add('escape', 'v')
    def _(event):
        " Scroll half page up. "
        scroll_half_page_up(event)

    @kb.add('pageup')
    def _(event):
        " Scroll one page up. "
        scroll_page_up(event)

    @kb.add('escape', '>')
    def _(event):
        " Scroll to bottom. "
        scroll_forward(event, count=1000000)

    @kb.add('escape', '<')
    def _(event):
        " Scroll to top. "
        scroll_backward(event, count=1000000)

    return ConditionalKeyBindings(kb, emacs_mode & buffer_has_focus)


def load_vi_page_navigation_bindings() ->KeyBindingsBase:
    """
    Key bindings, for scrolling up and down through pages.
    This are separate bindings, because GNU readline doesn't have them.
    """
    kb = KeyBindings()

    @kb.add('c-f')
    def _(event):
        " Scroll one page down. "
        scroll_page_down(event)

    @kb.add('c-b')
    def _(event):
        " Scroll one page up. "
        scroll_page_up(event)

    @kb.add('c-d')
    def _(event):
        " Scroll half page down. "
        scroll_half_page_down(event)

    @kb.add('c-u')
    def _(event):
        " Scroll half page up. "
        scroll_half_page_up(event)

    @kb.add('c-e')
    def _(event):
        " Scroll one line down. "
        scroll_one_line_down(event)

    @kb.add('c-y')
    def _(event):
        " Scroll one line up. "
        scroll_one_line_up(event)

    return ConditionalKeyBindings(kb, vi_mode & buffer_has_focus)
