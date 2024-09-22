"""
Key bindings for auto suggestion (for fish-style auto suggestion).
"""
from __future__ import annotations
import re
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition, emacs_mode
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
__all__ = ['load_auto_suggest_bindings']
E = KeyPressEvent


def load_auto_suggest_bindings() ->KeyBindings:
    """
    Key bindings for accepting auto suggestion text.

    (This has to come after the Vi bindings, because they also have an
    implementation for the "right arrow", but we really want the suggestion
    binding when a suggestion is available.)
    """
    pass
