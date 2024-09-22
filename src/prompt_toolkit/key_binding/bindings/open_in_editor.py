"""
Open in editor key bindings.
"""
from __future__ import annotations
from prompt_toolkit.filters import emacs_mode, has_selection, vi_navigation_mode
from ..key_bindings import KeyBindings, KeyBindingsBase, merge_key_bindings
from .named_commands import get_by_name
__all__ = ['load_open_in_editor_bindings',
    'load_emacs_open_in_editor_bindings', 'load_vi_open_in_editor_bindings']


def load_open_in_editor_bindings() ->KeyBindingsBase:
    """
    Load both the Vi and emacs key bindings for handling edit-and-execute-command.
    """
    pass


def load_emacs_open_in_editor_bindings() ->KeyBindings:
    """
    Pressing C-X C-E will open the buffer in an external editor.
    """
    pass


def load_vi_open_in_editor_bindings() ->KeyBindings:
    """
    Pressing 'v' in navigation mode will open the buffer in an external editor.
    """
    pass
