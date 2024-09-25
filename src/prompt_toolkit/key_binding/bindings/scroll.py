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
    window = event.app.layout.current_window
    if window:
        info = window.render_info
        if info:
            amount = info.window_height // 2 if half else info.window_height
            new_scroll = min(info.content_height - info.window_height,
                             info.vertical_scroll + amount)
            window.vertical_scroll = new_scroll


def scroll_backward(event: E, half: bool=False) ->None:
    """
    Scroll window up.
    """
    window = event.app.layout.current_window
    if window:
        info = window.render_info
        if info:
            amount = info.window_height // 2 if half else info.window_height
            new_scroll = max(0, info.vertical_scroll - amount)
            window.vertical_scroll = new_scroll


def scroll_half_page_down(event: E) ->None:
    """
    Same as ControlF, but only scroll half a page.
    """
    scroll_forward(event, half=True)


def scroll_half_page_up(event: E) ->None:
    """
    Same as ControlB, but only scroll half a page.
    """
    scroll_backward(event, half=True)


def scroll_one_line_down(event: E) ->None:
    """
    scroll_offset += 1
    """
    window = event.app.layout.current_window
    if window:
        info = window.render_info
        if info:
            new_scroll = min(info.content_height - info.window_height,
                             info.vertical_scroll + 1)
            window.vertical_scroll = new_scroll


def scroll_one_line_up(event: E) ->None:
    """
    scroll_offset -= 1
    """
    window = event.app.layout.current_window
    if window:
        info = window.render_info
        if info:
            new_scroll = max(0, info.vertical_scroll - 1)
            window.vertical_scroll = new_scroll


def scroll_page_down(event: E) ->None:
    """
    Scroll page down. (Prefer the cursor at the top of the page, after scrolling.)
    """
    window = event.app.layout.current_window
    b = event.app.current_buffer
    if window and b:
        info = window.render_info
        if info:
            # Scroll down one page, but keep one overlap line.
            overlap = 1
            new_scroll = min(info.content_height - info.window_height,
                             info.vertical_scroll + info.window_height - overlap)
            window.vertical_scroll = new_scroll

            # Put cursor at the top of the visible region.
            try:
                new_document_line = b.document.translate_row_col_to_index(
                    info.first_visible_line(), 0
                )
                b.cursor_position = new_document_line
            except IndexError:
                pass


def scroll_page_up(event: E) ->None:
    """
    Scroll page up. (Prefer the cursor at the bottom of the page, after scrolling.)
    """
    window = event.app.layout.current_window
    b = event.app.current_buffer
    if window and b:
        info = window.render_info
        if info:
            # Scroll up one page, but keep one overlap line.
            overlap = 1
            new_scroll = max(0, info.vertical_scroll - info.window_height + overlap)
            window.vertical_scroll = new_scroll

            # Put cursor at the bottom of the visible region.
            try:
                new_document_line = b.document.translate_row_col_to_index(
                    info.last_visible_line(), 0
                )
                b.cursor_position = new_document_line
            except IndexError:
                pass
