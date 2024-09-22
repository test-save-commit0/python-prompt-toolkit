"""
Utilities for manipulating formatted text.

When ``to_formatted_text`` has been called, we get a list of ``(style, text)``
tuples. This file contains functions for manipulating such a list.
"""
from __future__ import annotations
from typing import Iterable, cast
from prompt_toolkit.utils import get_cwidth
from .base import AnyFormattedText, OneStyleAndTextTuple, StyleAndTextTuples, to_formatted_text
__all__ = ['to_plain_text', 'fragment_list_len', 'fragment_list_width',
    'fragment_list_to_text', 'split_lines']


def to_plain_text(value: AnyFormattedText) ->str:
    """
    Turn any kind of formatted text back into plain text.
    """
    pass


def fragment_list_len(fragments: StyleAndTextTuples) ->int:
    """
    Return the amount of characters in this text fragment list.

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    pass


def fragment_list_width(fragments: StyleAndTextTuples) ->int:
    """
    Return the character width of this text fragment list.
    (Take double width characters into account.)

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    pass


def fragment_list_to_text(fragments: StyleAndTextTuples) ->str:
    """
    Concatenate all the text parts again.

    :param fragments: List of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    pass


def split_lines(fragments: Iterable[OneStyleAndTextTuple]) ->Iterable[
    StyleAndTextTuples]:
    """
    Take a single list of (style_str, text) tuples and yield one such list for each
    line. Just like str.split, this will yield at least one item.

    :param fragments: Iterable of ``(style_str, text)`` or
        ``(style_str, text, mouse_handler)`` tuples.
    """
    pass
