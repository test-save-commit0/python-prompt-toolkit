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
    kb = KeyBindings()

    @kb.add('c-x', 'c-e')
    def _(event: E) -> None:
        """Open editor."""
        event.app.run_system_command('editor')

    @kb.add('c-x', 'c-f')
    def _(event: E) -> None:
        """Find file."""
        event.app.run_system_command('find_file')

    @kb.add('c-x', 'c-s')
    def _(event: E) -> None:
        """Save file."""
        event.app.run_system_command('save_file')

    @kb.add('c-x', 'c-c')
    def _(event: E) -> None:
        """Quit."""
        event.app.exit()

    return ConditionalKeyBindings(kb, emacs_mode)


def load_emacs_shift_selection_bindings() ->KeyBindingsBase:
    """
    Bindings to select text with shift + cursor movements
    """
    kb = KeyBindings()

    @kb.add('s-left')
    def _(event: E) -> None:
        """Move cursor left and select."""
        buff = event.current_buffer
        buff.cursor_position += buff.document.get_cursor_left_position(count=event.arg)
        buff.start_selection()

    @kb.add('s-right')
    def _(event: E) -> None:
        """Move cursor right and select."""
        buff = event.current_buffer
        buff.cursor_position += buff.document.get_cursor_right_position(count=event.arg)
        buff.start_selection()

    @kb.add('s-up')
    def _(event: E) -> None:
        """Move cursor up and select."""
        buff = event.current_buffer
        buff.cursor_up(count=event.arg)
        buff.start_selection()

    @kb.add('s-down')
    def _(event: E) -> None:
        """Move cursor down and select."""
        buff = event.current_buffer
        buff.cursor_down(count=event.arg)
        buff.start_selection()

    return ConditionalKeyBindings(kb, emacs_mode & shift_selection_mode)
