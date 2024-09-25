from __future__ import annotations
from asyncio.events import AbstractEventLoop
from typing import TYPE_CHECKING, Any, TextIO
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app_or_none, get_app_session
from prompt_toolkit.application.run_in_terminal import run_in_terminal
from prompt_toolkit.formatted_text import FormattedText, StyleAndTextTuples, to_formatted_text
from prompt_toolkit.input import DummyInput
from prompt_toolkit.layout import Layout
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.renderer import print_formatted_text as renderer_print_formatted_text
from prompt_toolkit.styles import BaseStyle, StyleTransformation, default_pygments_style, default_ui_style, merge_styles
if TYPE_CHECKING:
    from prompt_toolkit.layout.containers import AnyContainer
__all__ = ['print_formatted_text', 'print_container', 'clear', 'set_title',
    'clear_title']


def print_formatted_text(*values: Any, sep: str=' ', end: str='\n', file: (
    TextIO | None)=None, flush: bool=False, style: (BaseStyle | None)=None,
    output: (Output | None)=None, color_depth: (ColorDepth | None)=None,
    style_transformation: (StyleTransformation | None)=None,
    include_default_pygments_style: bool=True) ->None:
    """
    ::

        print_formatted_text(*values, sep=' ', end='\\n', file=None, flush=False, style=None, output=None)

    Print text to stdout. This is supposed to be compatible with Python's print
    function, but supports printing of formatted text. You can pass a
    :class:`~prompt_toolkit.formatted_text.FormattedText`,
    :class:`~prompt_toolkit.formatted_text.HTML` or
    :class:`~prompt_toolkit.formatted_text.ANSI` object to print formatted
    text.

    * Print HTML as follows::

        print_formatted_text(HTML('<i>Some italic text</i> <ansired>This is red!</ansired>'))

        style = Style.from_dict({
            'hello': '#ff0066',
            'world': '#884444 italic',
        })
        print_formatted_text(HTML('<hello>Hello</hello> <world>world</world>!'), style=style)

    * Print a list of (style_str, text) tuples in the given style to the
      output.  E.g.::

        style = Style.from_dict({
            'hello': '#ff0066',
            'world': '#884444 italic',
        })
        fragments = FormattedText([
            ('class:hello', 'Hello'),
            ('class:world', 'World'),
        ])
        print_formatted_text(fragments, style=style)

    If you want to print a list of Pygments tokens, wrap it in
    :class:`~prompt_toolkit.formatted_text.PygmentsTokens` to do the
    conversion.

    If a prompt_toolkit `Application` is currently running, this will always
    print above the application or prompt (similar to `patch_stdout`). So,
    `print_formatted_text` will erase the current application, print the text,
    and render the application again.

    :param values: Any kind of printable object, or formatted string.
    :param sep: String inserted between values, default a space.
    :param end: String appended after the last value, default a newline.
    :param style: :class:`.Style` instance for the color scheme.
    :param include_default_pygments_style: `bool`. Include the default Pygments
        style when set to `True` (the default).
    """
    # Create a merged style
    merged_style = _create_merged_style(style, include_default_pygments_style)

    # Convert all values to formatted text
    fragments = []
    for i, value in enumerate(values):
        fragments.extend(to_formatted_text(value))
        if i < len(values) - 1:
            fragments.append(('', sep))

    fragments.append(('', end))

    # Get output object
    if output is None:
        if file is None:
            file = get_app_session().output
        output = create_output(stdout=file)

    # Get color depth
    if color_depth is None:
        color_depth = ColorDepth.default()

    # Create and print formatted text
    formatted_text = FormattedText(fragments)
    renderer_print_formatted_text(
        output, formatted_text, merged_style,
        color_depth=color_depth,
        style_transformation=style_transformation,
    )

    # Flush the output
    if flush:
        output.flush()


def print_container(container: AnyContainer, file: (TextIO | None)=None,
    style: (BaseStyle | None)=None, include_default_pygments_style: bool=True
    ) ->None:
    """
    Print any layout to the output in a non-interactive way.

    Example usage::

        from prompt_toolkit.widgets import Frame, TextArea
        print_container(
            Frame(TextArea(text='Hello world!')))
    """
    output = create_output(stdout=file)
    merged_style = _create_merged_style(style, include_default_pygments_style)

    app = Application(
        layout=Layout(container=container),
        output=output,
        style=merged_style,
    )

    with app.output.capture_stdout():
        app.run(in_thread=True)


def _create_merged_style(style: (BaseStyle | None),
    include_default_pygments_style: bool) ->BaseStyle:
    """
    Merge user defined style with built-in style.
    """
    styles = [default_ui_style()]
    if include_default_pygments_style:
        styles.append(default_pygments_style())
    if style:
        styles.append(style)
    return merge_styles(styles)


def clear() ->None:
    """
    Clear the screen.
    """
    output = get_app_session().output
    output.erase_screen()
    output.cursor_goto(0, 0)
    output.flush()


def set_title(text: str) ->None:
    """
    Set the terminal title.
    """
    output = get_app_session().output
    output.set_title(text)


def clear_title() ->None:
    """
    Erase the current title.
    """
    set_title('')
