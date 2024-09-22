from __future__ import annotations
import functools
from asyncio import get_running_loop
from typing import Any, Callable, Sequence, TypeVar
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer
from prompt_toolkit.eventloop import run_in_executor_with_context
from prompt_toolkit.filters import FilterOrBool
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import AnyContainer, HSplit
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.styles import BaseStyle
from prompt_toolkit.validation import Validator
from prompt_toolkit.widgets import Box, Button, CheckboxList, Dialog, Label, ProgressBar, RadioList, TextArea, ValidationToolbar
__all__ = ['yes_no_dialog', 'button_dialog', 'input_dialog',
    'message_dialog', 'radiolist_dialog', 'checkboxlist_dialog',
    'progress_dialog']


def yes_no_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    yes_text: str='Yes', no_text: str='No', style: (BaseStyle | None)=None
    ) ->Application[bool]:
    """
    Display a Yes/No dialog.
    Return a boolean.
    """
    pass


_T = TypeVar('_T')


def button_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    buttons: list[tuple[str, _T]]=[], style: (BaseStyle | None)=None
    ) ->Application[_T]:
    """
    Display a dialog with button choices (given as a list of tuples).
    Return the value associated with button.
    """
    pass


def input_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    ok_text: str='OK', cancel_text: str='Cancel', completer: (Completer |
    None)=None, validator: (Validator | None)=None, password: FilterOrBool=
    False, style: (BaseStyle | None)=None, default: str='') ->Application[str]:
    """
    Display a text input box.
    Return the given text, or None when cancelled.
    """
    pass


def message_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    ok_text: str='Ok', style: (BaseStyle | None)=None) ->Application[None]:
    """
    Display a simple message box and wait until the user presses enter.
    """
    pass


def radiolist_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    ok_text: str='Ok', cancel_text: str='Cancel', values: (Sequence[tuple[
    _T, AnyFormattedText]] | None)=None, default: (_T | None)=None, style:
    (BaseStyle | None)=None) ->Application[_T]:
    """
    Display a simple list of element the user can choose amongst.

    Only one element can be selected at a time using Arrow keys and Enter.
    The focus can be moved between the list and the Ok/Cancel button with tab.
    """
    pass


def checkboxlist_dialog(title: AnyFormattedText='', text: AnyFormattedText=
    '', ok_text: str='Ok', cancel_text: str='Cancel', values: (Sequence[
    tuple[_T, AnyFormattedText]] | None)=None, default_values: (Sequence[_T
    ] | None)=None, style: (BaseStyle | None)=None) ->Application[list[_T]]:
    """
    Display a simple list of element the user can choose multiple values amongst.

    Several elements can be selected at a time using Arrow keys and Enter.
    The focus can be moved between the list and the Ok/Cancel button with tab.
    """
    pass


def progress_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    run_callback: Callable[[Callable[[int], None], Callable[[str], None]],
    None]=lambda *a: None, style: (BaseStyle | None)=None) ->Application[None]:
    """
    :param run_callback: A function that receives as input a `set_percentage`
        function and it does the work.
    """
    pass


def _return_none() ->None:
    """Button handler that returns None."""
    pass
