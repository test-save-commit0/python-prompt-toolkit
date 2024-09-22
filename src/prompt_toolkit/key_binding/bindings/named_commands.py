"""
Key bindings which are also known by GNU Readline by the given names.

See: http://www.delorie.com/gnu/docs/readline/rlman_13.html
"""
from __future__ import annotations
from typing import Callable, TypeVar, Union, cast
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding.key_bindings import Binding, key_binding
from prompt_toolkit.key_binding.key_processor import KeyPress, KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.search import SearchDirection
from prompt_toolkit.selection import PasteMode
from .completion import display_completions_like_readline, generate_completions
__all__ = ['get_by_name']
_Handler = Callable[[KeyPressEvent], None]
_HandlerOrBinding = Union[_Handler, Binding]
_T = TypeVar('_T', bound=_HandlerOrBinding)
E = KeyPressEvent
_readline_commands: dict[str, Binding] = {}


def register(name: str) ->Callable[[_T], _T]:
    """
    Store handler in the `_readline_commands` dictionary.
    """
    pass


def get_by_name(name: str) ->Binding:
    """
    Return the handler for the (Readline) command with the given name.
    """
    pass


@register('beginning-of-buffer')
def beginning_of_buffer(event: E) ->None:
    """
    Move to the start of the buffer.
    """
    pass


@register('end-of-buffer')
def end_of_buffer(event: E) ->None:
    """
    Move to the end of the buffer.
    """
    pass


@register('beginning-of-line')
def beginning_of_line(event: E) ->None:
    """
    Move to the start of the current line.
    """
    pass


@register('end-of-line')
def end_of_line(event: E) ->None:
    """
    Move to the end of the line.
    """
    pass


@register('forward-char')
def forward_char(event: E) ->None:
    """
    Move forward a character.
    """
    pass


@register('backward-char')
def backward_char(event: E) ->None:
    """Move back a character."""
    pass


@register('forward-word')
def forward_word(event: E) ->None:
    """
    Move forward to the end of the next word. Words are composed of letters and
    digits.
    """
    pass


@register('backward-word')
def backward_word(event: E) ->None:
    """
    Move back to the start of the current or previous word. Words are composed
    of letters and digits.
    """
    pass


@register('clear-screen')
def clear_screen(event: E) ->None:
    """
    Clear the screen and redraw everything at the top of the screen.
    """
    pass


@register('redraw-current-line')
def redraw_current_line(event: E) ->None:
    """
    Refresh the current line.
    (Readline defines this command, but prompt-toolkit doesn't have it.)
    """
    pass


@register('accept-line')
def accept_line(event: E) ->None:
    """
    Accept the line regardless of where the cursor is.
    """
    pass


@register('previous-history')
def previous_history(event: E) ->None:
    """
    Move `back` through the history list, fetching the previous command.
    """
    pass


@register('next-history')
def next_history(event: E) ->None:
    """
    Move `forward` through the history list, fetching the next command.
    """
    pass


@register('beginning-of-history')
def beginning_of_history(event: E) ->None:
    """
    Move to the first line in the history.
    """
    pass


@register('end-of-history')
def end_of_history(event: E) ->None:
    """
    Move to the end of the input history, i.e., the line currently being entered.
    """
    pass


@register('reverse-search-history')
def reverse_search_history(event: E) ->None:
    """
    Search backward starting at the current line and moving `up` through
    the history as necessary. This is an incremental search.
    """
    pass


@register('end-of-file')
def end_of_file(event: E) ->None:
    """
    Exit.
    """
    pass


@register('delete-char')
def delete_char(event: E) ->None:
    """
    Delete character before the cursor.
    """
    pass


@register('backward-delete-char')
def backward_delete_char(event: E) ->None:
    """
    Delete the character behind the cursor.
    """
    pass


@register('self-insert')
def self_insert(event: E) ->None:
    """
    Insert yourself.
    """
    pass


@register('transpose-chars')
def transpose_chars(event: E) ->None:
    """
    Emulate Emacs transpose-char behavior: at the beginning of the buffer,
    do nothing.  At the end of a line or buffer, swap the characters before
    the cursor.  Otherwise, move the cursor right, and then swap the
    characters before the cursor.
    """
    pass


@register('uppercase-word')
def uppercase_word(event: E) ->None:
    """
    Uppercase the current (or following) word.
    """
    pass


@register('downcase-word')
def downcase_word(event: E) ->None:
    """
    Lowercase the current (or following) word.
    """
    pass


@register('capitalize-word')
def capitalize_word(event: E) ->None:
    """
    Capitalize the current (or following) word.
    """
    pass


@register('quoted-insert')
def quoted_insert(event: E) ->None:
    """
    Add the next character typed to the line verbatim. This is how to insert
    key sequences like C-q, for example.
    """
    pass


@register('kill-line')
def kill_line(event: E) ->None:
    """
    Kill the text from the cursor to the end of the line.

    If we are at the end of the line, this should remove the newline.
    (That way, it is possible to delete multiple lines by executing this
    command multiple times.)
    """
    pass


@register('kill-word')
def kill_word(event: E) ->None:
    """
    Kill from point to the end of the current word, or if between words, to the
    end of the next word. Word boundaries are the same as forward-word.
    """
    pass


@register('unix-word-rubout')
def unix_word_rubout(event: E, WORD: bool=True) ->None:
    """
    Kill the word behind point, using whitespace as a word boundary.
    Usually bound to ControlW.
    """
    pass


@register('backward-kill-word')
def backward_kill_word(event: E) ->None:
    """
    Kills the word before point, using "not a letter nor a digit" as a word boundary.
    Usually bound to M-Del or M-Backspace.
    """
    pass


@register('delete-horizontal-space')
def delete_horizontal_space(event: E) ->None:
    """
    Delete all spaces and tabs around point.
    """
    pass


@register('unix-line-discard')
def unix_line_discard(event: E) ->None:
    """
    Kill backward from the cursor to the beginning of the current line.
    """
    pass


@register('yank')
def yank(event: E) ->None:
    """
    Paste before cursor.
    """
    pass


@register('yank-nth-arg')
def yank_nth_arg(event: E) ->None:
    """
    Insert the first argument of the previous command. With an argument, insert
    the nth word from the previous command (start counting at 0).
    """
    pass


@register('yank-last-arg')
def yank_last_arg(event: E) ->None:
    """
    Like `yank_nth_arg`, but if no argument has been given, yank the last word
    of each line.
    """
    pass


@register('yank-pop')
def yank_pop(event: E) ->None:
    """
    Rotate the kill ring, and yank the new top. Only works following yank or
    yank-pop.
    """
    pass


@register('complete')
def complete(event: E) ->None:
    """
    Attempt to perform completion.
    """
    pass


@register('menu-complete')
def menu_complete(event: E) ->None:
    """
    Generate completions, or go to the next completion. (This is the default
    way of completing input in prompt_toolkit.)
    """
    pass


@register('menu-complete-backward')
def menu_complete_backward(event: E) ->None:
    """
    Move backward through the list of possible completions.
    """
    pass


@register('start-kbd-macro')
def start_kbd_macro(event: E) ->None:
    """
    Begin saving the characters typed into the current keyboard macro.
    """
    pass


@register('end-kbd-macro')
def end_kbd_macro(event: E) ->None:
    """
    Stop saving the characters typed into the current keyboard macro and save
    the definition.
    """
    pass


@register('call-last-kbd-macro')
@key_binding(record_in_macro=False)
def call_last_kbd_macro(event: E) ->None:
    """
    Re-execute the last keyboard macro defined, by making the characters in the
    macro appear as if typed at the keyboard.

    Notice that we pass `record_in_macro=False`. This ensures that the 'c-x e'
    key sequence doesn't appear in the recording itself. This function inserts
    the body of the called macro back into the KeyProcessor, so these keys will
    be added later on to the macro of their handlers have `record_in_macro=True`.
    """
    pass


@register('print-last-kbd-macro')
def print_last_kbd_macro(event: E) ->None:
    """
    Print the last keyboard macro.
    """
    pass


@register('undo')
def undo(event: E) ->None:
    """
    Incremental undo.
    """
    pass


@register('insert-comment')
def insert_comment(event: E) ->None:
    """
    Without numeric argument, comment all lines.
    With numeric argument, uncomment all lines.
    In any case accept the input.
    """
    pass


@register('vi-editing-mode')
def vi_editing_mode(event: E) ->None:
    """
    Switch to Vi editing mode.
    """
    pass


@register('emacs-editing-mode')
def emacs_editing_mode(event: E) ->None:
    """
    Switch to Emacs editing mode.
    """
    pass


@register('prefix-meta')
def prefix_meta(event: E) ->None:
    """
    Metafy the next character typed. This is for keyboards without a meta key.

    Sometimes people also want to bind other keys to Meta, e.g. 'jj'::

        key_bindings.add_key_binding('j', 'j', filter=ViInsertMode())(prefix_meta)
    """
    pass


@register('operate-and-get-next')
def operate_and_get_next(event: E) ->None:
    """
    Accept the current line for execution and fetch the next line relative to
    the current line from the history for editing.
    """
    pass


@register('edit-and-execute-command')
def edit_and_execute(event: E) ->None:
    """
    Invoke an editor on the current command line, and accept the result.
    """
    pass
