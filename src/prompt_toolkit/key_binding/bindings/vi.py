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
        return (min(self.start, self.end), max(self.start, self.end))

    def operator_range(self, document: Document) ->tuple[int, int]:
        """
        Return a (start, end) tuple with start <= end that indicates the range
        operators should operate on.
        `buffer` is used to get start and end of line positions.

        This should return something that can be used in a slice, so the `end`
        position is *not* included.
        """
        start, end = self.sorted()
        cursor_position = document.cursor_position

        if self.type == TextObjectType.EXCLUSIVE:
            return (cursor_position + start, cursor_position + end + 1)
        elif self.type == TextObjectType.INCLUSIVE:
            return (cursor_position + start, cursor_position + end + 1)
        elif self.type == TextObjectType.LINEWISE:
            start_line = document.line_count - 1 if start < 0 else document.cursor_position_row + start
            end_line = document.line_count - 1 if end < 0 else document.cursor_position_row + end
            return (document.get_start_of_line_position(start_line),
                    min(document.get_end_of_line_position(end_line) + 1, len(document.text)))
        else:  # BLOCK
            return (cursor_position + start, cursor_position + end + 1)

    def get_line_numbers(self, buffer: Buffer) ->tuple[int, int]:
        """
        Return a (start_line, end_line) pair.
        """
        document = buffer.document
        start, end = self.sorted()
        cursor_row = document.cursor_position_row

        if self.type in (TextObjectType.EXCLUSIVE, TextObjectType.INCLUSIVE):
            start_line = document.translate_row_col_to_index(cursor_row + start, 0)
            end_line = document.translate_row_col_to_index(cursor_row + end, 0)
        elif self.type == TextObjectType.LINEWISE:
            start_line = max(0, cursor_row + start)
            end_line = min(document.line_count - 1, cursor_row + end)
        else:  # BLOCK
            start_line = cursor_row
            end_line = cursor_row + end

        return (start_line, end_line)

    def cut(self, buffer: Buffer) ->tuple[Document, ClipboardData]:
        """
        Turn text object into `ClipboardData` instance.
        """
        start, end = self.operator_range(buffer.document)
        text = buffer.text[start:end]
        
        if self.type == TextObjectType.LINEWISE:
            text += '\n'
        
        new_document = Document(
            text=buffer.text[:start] + buffer.text[end:],
            cursor_position=start
        )
        
        return new_document, ClipboardData(text, self.type)


TextObjectFunction = Callable[[E], TextObject]
_TOF = TypeVar('_TOF', bound=TextObjectFunction)


def create_text_object_decorator(key_bindings: KeyBindings) ->Callable[...,
    Callable[[_TOF], _TOF]]:
    """
    Create a decorator that can be used to register Vi text object implementations.
    """
    def decorator(*keys: str, filter: Filter=Always(), eager: bool=False):
        def wrapper(func: _TOF) -> _TOF:
            @key_bindings.add(*keys, filter=filter & vi_waiting_for_text_object_mode, eager=eager)
            def _(event: E) -> None:
                if event.app.vi_state.operator_func:
                    text_object = func(event)
                    event.app.vi_state.operator_func(event, text_object)
                    event.app.vi_state.operator_func = None
                    event.app.vi_state.operator_arg = None
                else:
                    # Move cursor.
                    text_object = func(event)
                    start, end = text_object.operator_range(event.app.current_buffer.document)
                    event.app.current_buffer.cursor_position += start
            return func
        return wrapper
    return decorator


OperatorFunction = Callable[[E, TextObject], None]
_OF = TypeVar('_OF', bound=OperatorFunction)


def create_operator_decorator(key_bindings: KeyBindings) ->Callable[...,
    Callable[[_OF], _OF]]:
    """
    Create a decorator that can be used for registering Vi operators.
    """
    def decorator(*keys: str, filter: Filter=Always(), eager: bool=False):
        def wrapper(func: _OF) -> _OF:
            @key_bindings.add(*keys, filter=filter & vi_navigation_mode, eager=eager)
            def _(event: E) -> None:
                event.app.vi_state.operator_func = func
                event.app.vi_state.operator_arg = event.arg

            return func
        return wrapper
    return decorator


def load_vi_bindings() ->KeyBindingsBase:
    """
    Vi extensions.

    # Overview of Readline Vi commands:
    # http://www.catonmat.net/download/bash-vi-editing-mode-cheat-sheet.pdf
    """
    pass
