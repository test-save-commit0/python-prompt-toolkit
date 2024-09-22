"""
Data structures for the selection.
"""
from __future__ import annotations
from enum import Enum
__all__ = ['SelectionType', 'PasteMode', 'SelectionState']


class SelectionType(Enum):
    """
    Type of selection.
    """
    CHARACTERS = 'CHARACTERS'
    LINES = 'LINES'
    BLOCK = 'BLOCK'


class PasteMode(Enum):
    EMACS = 'EMACS'
    VI_AFTER = 'VI_AFTER'
    VI_BEFORE = 'VI_BEFORE'


class SelectionState:
    """
    State of the current selection.

    :param original_cursor_position: int
    :param type: :class:`~.SelectionType`
    """

    def __init__(self, original_cursor_position: int=0, type: SelectionType
        =SelectionType.CHARACTERS) ->None:
        self.original_cursor_position = original_cursor_position
        self.type = type
        self.shift_mode = False

    def __repr__(self) ->str:
        return '{}(original_cursor_position={!r}, type={!r})'.format(self.
            __class__.__name__, self.original_cursor_position, self.type)
