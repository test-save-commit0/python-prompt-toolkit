from __future__ import annotations
import codecs
import string
from enum import Enum
from itertools import accumulate
from typing import Callable, Iterable, Tuple, TypeVar
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer, indent, reshape_text, unindent
from prompt_toolkit.clipboard import ClipboardData
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Always, Condition, Filter, has_arg, is_read_only, is_searching
from prompt_toolkit.filters.app import in_paste_mode, is_multiline, vi_digraph_mode, vi_insert_mode, vi_insert_multiple_mode, vi_mode, vi_navigation_mode, vi_recording_macro, vi_replace_mode, vi_replace_single_mode, vi_search_direction_reversed, vi_selection_mode, vi_waiting_for_text_object_mode
from prompt_toolkit.input.vt100_parser import Vt100Parser
from prompt_toolkit.key_binding.digraphs import DIGRAPHS
from prompt_toolkit.key_binding.key_processor import KeyPress, KeyPressEvent
from prompt_toolkit.key_binding.vi_state import CharacterFind, InputMode
from prompt_toolkit.keys import Keys
from prompt_toolkit.search import SearchDirection
from prompt_toolkit.selection import PasteMode, SelectionState, SelectionType
from ..key_bindings import ConditionalKeyBindings, KeyBindings, KeyBindingsBase
from .named_commands import get_by_name
__all__ = ['load_vi_bindings', 'load_vi_search_bindings']
E = KeyPressEvent
ascii_lowercase = string.ascii_lowercase
vi_register_names = ascii_lowercase + '0123456789'


class TextObjectType(Enum):
    EXCLUSIVE = 'EXCLUSIVE'
    INCLUSIVE = 'INCLUSIVE'
    LINEWISE = 'LINEWISE'
    BLOCK = 'BLOCK'


class TextObject:
    """
    Return struct for functions wrapped in ``text_object``.
    Both `start` and `end` are relative to the current cursor position.
    """

    def __init__(self, start: int, end: int=0, type: TextObjectType=
        TextObjectType.EXCLUSIVE):
        self.start = start
        self.end = end
        self.type = type

    def sorted(self) ->tuple[int, int]:
        """
        Return a (start, end) tuple where start <= end.
        """
        pass

    def operator_range(self, document: Document) ->tuple[int, int]:
        """
        Return a (start, end) tuple with start <= end that indicates the range
        operators should operate on.
        `buffer` is used to get start and end of line positions.

        This should return something that can be used in a slice, so the `end`
        position is *not* included.
        """
        pass

    def get_line_numbers(self, buffer: Buffer) ->tuple[int, int]:
        """
        Return a (start_line, end_line) pair.
        """
        pass

    def cut(self, buffer: Buffer) ->tuple[Document, ClipboardData]:
        """
        Turn text object into `ClipboardData` instance.
        """
        pass


TextObjectFunction = Callable[[E], TextObject]
_TOF = TypeVar('_TOF', bound=TextObjectFunction)


def create_text_object_decorator(key_bindings: KeyBindings) ->Callable[...,
    Callable[[_TOF], _TOF]]:
    """
    Create a decorator that can be used to register Vi text object implementations.
    """
    pass


OperatorFunction = Callable[[E, TextObject], None]
_OF = TypeVar('_OF', bound=OperatorFunction)


def create_operator_decorator(key_bindings: KeyBindings) ->Callable[...,
    Callable[[_OF], _OF]]:
    """
    Create a decorator that can be used for registering Vi operators.
    """
    pass


def load_vi_bindings() ->KeyBindingsBase:
    """
    Vi extensions.

    # Overview of Readline Vi commands:
    # http://www.catonmat.net/download/bash-vi-editing-mode-cheat-sheet.pdf
    """
    pass
