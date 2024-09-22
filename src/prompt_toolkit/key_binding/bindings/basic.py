from __future__ import annotations
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition, emacs_insert_mode, has_selection, in_paste_mode, is_multiline, vi_insert_mode
from prompt_toolkit.key_binding.key_processor import KeyPress, KeyPressEvent
from prompt_toolkit.keys import Keys
from ..key_bindings import KeyBindings
from .named_commands import get_by_name
__all__ = ['load_basic_bindings']
E = KeyPressEvent


def if_no_repeat(event: E) ->bool:
    """Callable that returns True when the previous event was delivered to
    another handler."""
    pass
