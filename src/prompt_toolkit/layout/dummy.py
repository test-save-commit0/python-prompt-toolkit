"""
Dummy layout. Used when somebody creates an `Application` without specifying a
`Layout`.
"""
from __future__ import annotations
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from .containers import Window
from .controls import FormattedTextControl
from .dimension import D
from .layout import Layout
__all__ = ['create_dummy_layout']
E = KeyPressEvent


def create_dummy_layout() ->Layout:
    """
    Create a dummy layout for use in an 'Application' that doesn't have a
    layout specified. When ENTER is pressed, the application quits.
    """
    kb = KeyBindings()

    @kb.add('enter')
    def _(event: E) -> None:
        " Quit when enter is pressed. "
        event.app.exit()

    dummy_text = HTML(
        '<style bg="ansiblack" fg="ansiwhite">'
        'This is a dummy layout. '
        'You did not provide a layout to your Application.\n'
        'Press ENTER to quit.'
        '</style>'
    )

    window = Window(
        FormattedTextControl(dummy_text),
        height=D(min=1),
        key_bindings=kb,
    )

    return Layout(window)
