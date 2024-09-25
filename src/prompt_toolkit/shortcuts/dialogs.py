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
    def yes_handler() -> None:
        get_app().exit(result=True)

    def no_handler() -> None:
        get_app().exit(result=False)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[
            Button(text=yes_text, handler=yes_handler),
            Button(text=no_text, handler=no_handler),
        ],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            focus_next,
            focus_previous,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )


_T = TypeVar('_T')


def button_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    buttons: list[tuple[str, _T]]=[], style: (BaseStyle | None)=None
    ) ->Application[_T]:
    """
    Display a dialog with button choices (given as a list of tuples).
    Return the value associated with button.
    """
    def button_handler(value: _T) -> None:
        get_app().exit(result=value)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[
            Button(text=button_text, handler=functools.partial(button_handler, value))
            for button_text, value in buttons
        ],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            focus_next,
            focus_previous,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )


def input_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    ok_text: str='OK', cancel_text: str='Cancel', completer: (Completer |
    None)=None, validator: (Validator | None)=None, password: FilterOrBool=
    False, style: (BaseStyle | None)=None, default: str='') ->Application[str]:
    """
    Display a text input box.
    Return the given text, or None when cancelled.
    """
    def accept(buf: Buffer) -> bool:
        get_app().layout.focus(ok_button)
        return True

    def ok_handler() -> None:
        get_app().exit(result=textfield.text)

    def cancel_handler() -> None:
        get_app().exit(result=None)

    textfield = TextArea(
        completer=completer,
        validator=validator,
        password=password,
        multiline=False,
        width=D(preferred=40),
        accept_handler=accept,
        default=default,
    )

    ok_button = Button(text=ok_text, handler=ok_handler)
    cancel_button = Button(text=cancel_text, handler=cancel_handler)

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            textfield,
            ValidationToolbar(),
        ]),
        buttons=[ok_button, cancel_button],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            focus_next,
            focus_previous,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )


def message_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    ok_text: str='Ok', style: (BaseStyle | None)=None) ->Application[None]:
    """
    Display a simple message box and wait until the user presses enter.
    """
    def ok_handler() -> None:
        get_app().exit(result=None)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[Button(text=ok_text, handler=ok_handler)],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            focus_next,
            focus_previous,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )


def radiolist_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    ok_text: str='Ok', cancel_text: str='Cancel', values: (Sequence[tuple[
    _T, AnyFormattedText]] | None)=None, default: (_T | None)=None, style:
    (BaseStyle | None)=None) ->Application[_T]:
    """
    Display a simple list of element the user can choose amongst.

    Only one element can be selected at a time using Arrow keys and Enter.
    The focus can be moved between the list and the Ok/Cancel button with tab.
    """
    def ok_handler() -> None:
        get_app().exit(result=radio_list.current_value)

    def cancel_handler() -> None:
        get_app().exit(result=None)

    radio_list = RadioList(values or [], default=default)

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            radio_list,
        ]),
        buttons=[
            Button(text=ok_text, handler=ok_handler),
            Button(text=cancel_text, handler=cancel_handler),
        ],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            focus_next,
            focus_previous,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )


def checkboxlist_dialog(title: AnyFormattedText='', text: AnyFormattedText=
    '', ok_text: str='Ok', cancel_text: str='Cancel', values: (Sequence[
    tuple[_T, AnyFormattedText]] | None)=None, default_values: (Sequence[_T
    ] | None)=None, style: (BaseStyle | None)=None) ->Application[list[_T]]:
    """
    Display a simple list of element the user can choose multiple values amongst.

    Several elements can be selected at a time using Arrow keys and Enter.
    The focus can be moved between the list and the Ok/Cancel button with tab.
    """
    def ok_handler() -> None:
        get_app().exit(result=checkbox_list.current_values)

    def cancel_handler() -> None:
        get_app().exit(result=None)

    checkbox_list = CheckboxList(values or [], default_values=default_values or [])

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            checkbox_list,
        ]),
        buttons=[
            Button(text=ok_text, handler=ok_handler),
            Button(text=cancel_text, handler=cancel_handler),
        ],
        with_background=True,
    )

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            focus_next,
            focus_previous,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True,
    )


def progress_dialog(title: AnyFormattedText='', text: AnyFormattedText='',
    run_callback: Callable[[Callable[[int], None], Callable[[str], None]],
    None]=lambda *a: None, style: (BaseStyle | None)=None) ->Application[None]:
    """
    :param run_callback: A function that receives as input a `set_percentage`
        function and it does the work.
    """
    progressbar = ProgressBar()
    text_area = TextArea(
        focusable=False,
        multiline=True,
        width=D(preferred=40),
        height=D(preferred=3),
    )

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            Box(progressbar, padding=1),
            text_area,
        ]),
        with_background=True,
    )

    app = Application(
        layout=Layout(dialog),
        key_bindings=load_key_bindings(),
        mouse_support=True,
        style=style,
        full_screen=True,
    )

    def set_percentage(value: int) -> None:
        progressbar.percentage = value
        app.invalidate()

    def set_text(text: str) -> None:
        text_area.text = text
        app.invalidate()

    async def run_in_executor() -> None:
        await run_in_executor_with_context(
            run_callback, set_percentage, set_text
        )
        app.exit()

    app.after_create = lambda: get_running_loop().create_task(run_in_executor())

    return app


def _return_none() ->None:
    """Button handler that returns None."""
    get_app().exit(result=None)
