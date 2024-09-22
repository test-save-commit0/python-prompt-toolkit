from __future__ import annotations
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer, indent, unindent
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.filters import Condition, emacs_insert_mode, emacs_mode, has_arg, has_selection, in_paste_mode, is_multiline, is_read_only, shift_selection_mode, vi_search_direction_reversed
from prompt_toolkit.key_binding.key_bindings import Binding
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.selection import SelectionType
from ..key_bindings import ConditionalKeyBindings, KeyBindings, KeyBindingsBase
from .named_commands import get_by_name
__all__ = ['load_emacs_bindings', 'load_emacs_search_bindings',
    'load_emacs_shift_selection_bindings']
E = KeyPressEvent


def load_emacs_bindings() ->KeyBindingsBase:
    """
    Some e-macs extensions.
    """
    pass


def load_emacs_shift_selection_bindings() ->KeyBindingsBase:
    """
    Bindings to select text with shift + cursor movements
    """
    pass
