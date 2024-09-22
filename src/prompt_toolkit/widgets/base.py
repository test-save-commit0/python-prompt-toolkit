"""
Collection of reusable components for building full screen applications.

All of these widgets implement the ``__pt_container__`` method, which makes
them usable in any situation where we are expecting a `prompt_toolkit`
container object.

.. warning::

    At this point, the API for these widgets is considered unstable, and can
    potentially change between minor releases (we try not too, but no
    guarantees are made yet). The public API in
    `prompt_toolkit.shortcuts.dialogs` on the other hand is considered stable.
"""
from __future__ import annotations
from functools import partial
from typing import Callable, Generic, Sequence, TypeVar
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import AutoSuggest, DynamicAutoSuggest
from prompt_toolkit.buffer import Buffer, BufferAcceptHandler
from prompt_toolkit.completion import Completer, DynamicCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition, FilterOrBool, has_focus, is_done, is_true, to_filter
from prompt_toolkit.formatted_text import AnyFormattedText, StyleAndTextTuples, Template, to_formatted_text
from prompt_toolkit.formatted_text.utils import fragment_list_to_text
from prompt_toolkit.history import History
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import AnyContainer, ConditionalContainer, Container, DynamicContainer, Float, FloatContainer, HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl, GetLinePrefixCallable
from prompt_toolkit.layout.dimension import AnyDimension, to_dimension
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.layout.margins import ConditionalMargin, NumberedMargin, ScrollbarMargin
from prompt_toolkit.layout.processors import AppendAutoSuggestion, BeforeInput, ConditionalProcessor, PasswordProcessor, Processor
from prompt_toolkit.lexers import DynamicLexer, Lexer
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.validation import DynamicValidator, Validator
from .toolbars import SearchToolbar
__all__ = ['TextArea', 'Label', 'Button', 'Frame', 'Shadow', 'Box',
    'VerticalLine', 'HorizontalLine', 'RadioList', 'CheckboxList',
    'Checkbox', 'ProgressBar']
E = KeyPressEvent


class Border:
    """Box drawing characters. (Thin)"""
    HORIZONTAL = '─'
    VERTICAL = '│'
    TOP_LEFT = '┌'
    TOP_RIGHT = '┐'
    BOTTOM_LEFT = '└'
    BOTTOM_RIGHT = '┘'


class TextArea:
    """
    A simple input field.

    This is a higher level abstraction on top of several other classes with
    sane defaults.

    This widget does have the most common options, but it does not intend to
    cover every single use case. For more configurations options, you can
    always build a text area manually, using a
    :class:`~prompt_toolkit.buffer.Buffer`,
    :class:`~prompt_toolkit.layout.BufferControl` and
    :class:`~prompt_toolkit.layout.Window`.

    Buffer attributes:

    :param text: The initial text.
    :param multiline: If True, allow multiline input.
    :param completer: :class:`~prompt_toolkit.completion.Completer` instance
        for auto completion.
    :param complete_while_typing: Boolean.
    :param accept_handler: Called when `Enter` is pressed (This should be a
        callable that takes a buffer as input).
    :param history: :class:`~prompt_toolkit.history.History` instance.
    :param auto_suggest: :class:`~prompt_toolkit.auto_suggest.AutoSuggest`
        instance for input suggestions.

    BufferControl attributes:

    :param password: When `True`, display using asterisks.
    :param focusable: When `True`, allow this widget to receive the focus.
    :param focus_on_click: When `True`, focus after mouse click.
    :param input_processors: `None` or a list of
        :class:`~prompt_toolkit.layout.Processor` objects.
    :param validator: `None` or a :class:`~prompt_toolkit.validation.Validator`
        object.

    Window attributes:

    :param lexer: :class:`~prompt_toolkit.lexers.Lexer` instance for syntax
        highlighting.
    :param wrap_lines: When `True`, don't scroll horizontally, but wrap lines.
    :param width: Window width. (:class:`~prompt_toolkit.layout.Dimension` object.)
    :param height: Window height. (:class:`~prompt_toolkit.layout.Dimension` object.)
    :param scrollbar: When `True`, display a scroll bar.
    :param style: A style string.
    :param dont_extend_width: When `True`, don't take up more width then the
                              preferred width reported by the control.
    :param dont_extend_height: When `True`, don't take up more width then the
                               preferred height reported by the control.
    :param get_line_prefix: None or a callable that returns formatted text to
        be inserted before a line. It takes a line number (int) and a
        wrap_count and returns formatted text. This can be used for
        implementation of line continuations, things like Vim "breakindent" and
        so on.

    Other attributes:

    :param search_field: An optional `SearchToolbar` object.
    """

    def __init__(self, text: str='', multiline: FilterOrBool=True, password:
        FilterOrBool=False, lexer: (Lexer | None)=None, auto_suggest: (
        AutoSuggest | None)=None, completer: (Completer | None)=None,
        complete_while_typing: FilterOrBool=True, validator: (Validator |
        None)=None, accept_handler: (BufferAcceptHandler | None)=None,
        history: (History | None)=None, focusable: FilterOrBool=True,
        focus_on_click: FilterOrBool=False, wrap_lines: FilterOrBool=True,
        read_only: FilterOrBool=False, width: AnyDimension=None, height:
        AnyDimension=None, dont_extend_height: FilterOrBool=False,
        dont_extend_width: FilterOrBool=False, line_numbers: bool=False,
        get_line_prefix: (GetLinePrefixCallable | None)=None, scrollbar:
        bool=False, style: str='', search_field: (SearchToolbar | None)=
        None, preview_search: FilterOrBool=True, prompt: AnyFormattedText=
        '', input_processors: (list[Processor] | None)=None, name: str=''
        ) ->None:
        if search_field is None:
            search_control = None
        elif isinstance(search_field, SearchToolbar):
            search_control = search_field.control
        if input_processors is None:
            input_processors = []
        self.completer = completer
        self.complete_while_typing = complete_while_typing
        self.lexer = lexer
        self.auto_suggest = auto_suggest
        self.read_only = read_only
        self.wrap_lines = wrap_lines
        self.validator = validator
        self.buffer = Buffer(document=Document(text, 0), multiline=
            multiline, read_only=Condition(lambda : is_true(self.read_only)
            ), completer=DynamicCompleter(lambda : self.completer),
            complete_while_typing=Condition(lambda : is_true(self.
            complete_while_typing)), validator=DynamicValidator(lambda :
            self.validator), auto_suggest=DynamicAutoSuggest(lambda : self.
            auto_suggest), accept_handler=accept_handler, history=history,
            name=name)
        self.control = BufferControl(buffer=self.buffer, lexer=DynamicLexer
            (lambda : self.lexer), input_processors=[ConditionalProcessor(
            AppendAutoSuggestion(), has_focus(self.buffer) & ~is_done),
            ConditionalProcessor(processor=PasswordProcessor(), filter=
            to_filter(password)), BeforeInput(prompt, style=
            'class:text-area.prompt')] + input_processors,
            search_buffer_control=search_control, preview_search=
            preview_search, focusable=focusable, focus_on_click=focus_on_click)
        if multiline:
            if scrollbar:
                right_margins = [ScrollbarMargin(display_arrows=True)]
            else:
                right_margins = []
            if line_numbers:
                left_margins = [NumberedMargin()]
            else:
                left_margins = []
        else:
            height = D.exact(1)
            left_margins = []
            right_margins = []
        style = 'class:text-area ' + style
        if height is None:
            height = D(min=1)
        self.window = Window(height=height, width=width, dont_extend_height
            =dont_extend_height, dont_extend_width=dont_extend_width,
            content=self.control, style=style, wrap_lines=Condition(lambda :
            is_true(self.wrap_lines)), left_margins=left_margins,
            right_margins=right_margins, get_line_prefix=get_line_prefix)

    @property
    def text(self) ->str:
        """
        The `Buffer` text.
        """
        pass

    @property
    def document(self) ->Document:
        """
        The `Buffer` document (text + cursor position).
        """
        pass

    @property
    def accept_handler(self) ->(BufferAcceptHandler | None):
        """
        The accept handler. Called when the user accepts the input.
        """
        pass

    def __pt_container__(self) ->Container:
        return self.window


class Label:
    """
    Widget that displays the given text. It is not editable or focusable.

    :param text: Text to display. Can be multiline. All value types accepted by
        :class:`prompt_toolkit.layout.FormattedTextControl` are allowed,
        including a callable.
    :param style: A style string.
    :param width: When given, use this width, rather than calculating it from
        the text size.
    :param dont_extend_width: When `True`, don't take up more width than
                              preferred, i.e. the length of the longest line of
                              the text, or value of `width` parameter, if
                              given. `True` by default
    :param dont_extend_height: When `True`, don't take up more width than the
                               preferred height, i.e. the number of lines of
                               the text. `False` by default.
    """

    def __init__(self, text: AnyFormattedText, style: str='', width:
        AnyDimension=None, dont_extend_height: bool=True, dont_extend_width:
        bool=False, align: (WindowAlign | Callable[[], WindowAlign])=
        WindowAlign.LEFT, wrap_lines: FilterOrBool=True) ->None:
        self.text = text

        def get_width() ->AnyDimension:
            if width is None:
                text_fragments = to_formatted_text(self.text)
                text = fragment_list_to_text(text_fragments)
                if text:
                    longest_line = max(get_cwidth(line) for line in text.
                        splitlines())
                else:
                    return D(preferred=0)
                return D(preferred=longest_line)
            else:
                return width
        self.formatted_text_control = FormattedTextControl(text=lambda :
            self.text)
        self.window = Window(content=self.formatted_text_control, width=
            get_width, height=D(min=1), style='class:label ' + style,
            dont_extend_height=dont_extend_height, dont_extend_width=
            dont_extend_width, align=align, wrap_lines=wrap_lines)

    def __pt_container__(self) ->Container:
        return self.window


class Button:
    """
    Clickable button.

    :param text: The caption for the button.
    :param handler: `None` or callable. Called when the button is clicked. No
        parameters are passed to this callable. Use for instance Python's
        `functools.partial` to pass parameters to this callable if needed.
    :param width: Width of the button.
    """

    def __init__(self, text: str, handler: (Callable[[], None] | None)=None,
        width: int=12, left_symbol: str='<', right_symbol: str='>') ->None:
        self.text = text
        self.left_symbol = left_symbol
        self.right_symbol = right_symbol
        self.handler = handler
        self.width = width
        self.control = FormattedTextControl(self._get_text_fragments,
            key_bindings=self._get_key_bindings(), focusable=True)

        def get_style() ->str:
            if get_app().layout.has_focus(self):
                return 'class:button.focused'
            else:
                return 'class:button'
        self.window = Window(self.control, align=WindowAlign.CENTER, height
            =1, width=width, style=get_style, dont_extend_width=False,
            dont_extend_height=True)

    def _get_key_bindings(self) ->KeyBindings:
        """Key bindings for the Button."""
        pass

    def __pt_container__(self) ->Container:
        return self.window


class Frame:
    """
    Draw a border around any container, optionally with a title text.

    Changing the title and body of the frame is possible at runtime by
    assigning to the `body` and `title` attributes of this class.

    :param body: Another container object.
    :param title: Text to be displayed in the top of the frame (can be formatted text).
    :param style: Style string to be applied to this widget.
    """

    def __init__(self, body: AnyContainer, title: AnyFormattedText='',
        style: str='', width: AnyDimension=None, height: AnyDimension=None,
        key_bindings: (KeyBindings | None)=None, modal: bool=False) ->None:
        self.title = title
        self.body = body
        fill = partial(Window, style='class:frame.border')
        style = 'class:frame ' + style
        top_row_with_title = VSplit([fill(width=1, height=1, char=Border.
            TOP_LEFT), fill(char=Border.HORIZONTAL), fill(width=1, height=1,
            char='|'), Label(lambda : Template(' {} ').format(self.title),
            style='class:frame.label', dont_extend_width=True), fill(width=
            1, height=1, char='|'), fill(char=Border.HORIZONTAL), fill(
            width=1, height=1, char=Border.TOP_RIGHT)], height=1)
        top_row_without_title = VSplit([fill(width=1, height=1, char=Border
            .TOP_LEFT), fill(char=Border.HORIZONTAL), fill(width=1, height=
            1, char=Border.TOP_RIGHT)], height=1)

        @Condition
        def has_title() ->bool:
            return bool(self.title)
        self.container = HSplit([ConditionalContainer(content=
            top_row_with_title, filter=has_title), ConditionalContainer(
            content=top_row_without_title, filter=~has_title), VSplit([fill
            (width=1, char=Border.VERTICAL), DynamicContainer(lambda : self
            .body), fill(width=1, char=Border.VERTICAL)], padding=0),
            VSplit([fill(width=1, height=1, char=Border.BOTTOM_LEFT), fill(
            char=Border.HORIZONTAL), fill(width=1, height=1, char=Border.
            BOTTOM_RIGHT)], height=1)], width=width, height=height, style=
            style, key_bindings=key_bindings, modal=modal)

    def __pt_container__(self) ->Container:
        return self.container


class Shadow:
    """
    Draw a shadow underneath/behind this container.
    (This applies `class:shadow` the the cells under the shadow. The Style
    should define the colors for the shadow.)

    :param body: Another container object.
    """

    def __init__(self, body: AnyContainer) ->None:
        self.container = FloatContainer(content=body, floats=[Float(bottom=
            -1, height=1, left=1, right=-1, transparent=True, content=
            Window(style='class:shadow')), Float(bottom=-1, top=1, width=1,
            right=-1, transparent=True, content=Window(style='class:shadow'))])

    def __pt_container__(self) ->Container:
        return self.container


class Box:
    """
    Add padding around a container.

    This also makes sure that the parent can provide more space than required by
    the child. This is very useful when wrapping a small element with a fixed
    size into a ``VSplit`` or ``HSplit`` object. The ``HSplit`` and ``VSplit``
    try to make sure to adapt respectively the width and height, possibly
    shrinking other elements. Wrapping something in a ``Box`` makes it flexible.

    :param body: Another container object.
    :param padding: The margin to be used around the body. This can be
        overridden by `padding_left`, padding_right`, `padding_top` and
        `padding_bottom`.
    :param style: A style string.
    :param char: Character to be used for filling the space around the body.
        (This is supposed to be a character with a terminal width of 1.)
    """

    def __init__(self, body: AnyContainer, padding: AnyDimension=None,
        padding_left: AnyDimension=None, padding_right: AnyDimension=None,
        padding_top: AnyDimension=None, padding_bottom: AnyDimension=None,
        width: AnyDimension=None, height: AnyDimension=None, style: str='',
        char: (None | str | Callable[[], str])=None, modal: bool=False,
        key_bindings: (KeyBindings | None)=None) ->None:
        if padding is None:
            padding = D(preferred=0)

        def get(value: AnyDimension) ->D:
            if value is None:
                value = padding
            return to_dimension(value)
        self.padding_left = get(padding_left)
        self.padding_right = get(padding_right)
        self.padding_top = get(padding_top)
        self.padding_bottom = get(padding_bottom)
        self.body = body
        self.container = HSplit([Window(height=self.padding_top, char=char),
            VSplit([Window(width=self.padding_left, char=char), body,
            Window(width=self.padding_right, char=char)]), Window(height=
            self.padding_bottom, char=char)], width=width, height=height,
            style=style, modal=modal, key_bindings=None)

    def __pt_container__(self) ->Container:
        return self.container


_T = TypeVar('_T')


class _DialogList(Generic[_T]):
    """
    Common code for `RadioList` and `CheckboxList`.
    """
    open_character: str = ''
    close_character: str = ''
    container_style: str = ''
    default_style: str = ''
    selected_style: str = ''
    checked_style: str = ''
    multiple_selection: bool = False
    show_scrollbar: bool = True

    def __init__(self, values: Sequence[tuple[_T, AnyFormattedText]],
        default_values: (Sequence[_T] | None)=None) ->None:
        assert len(values) > 0
        default_values = default_values or []
        self.values = values
        keys: list[_T] = [value for value, _ in values]
        self.current_values: list[_T] = [value for value in default_values if
            value in keys]
        self.current_value: _T = default_values[0] if len(default_values
            ) and default_values[0] in keys else values[0][0]
        if len(self.current_values) > 0:
            self._selected_index = keys.index(self.current_values[0])
        else:
            self._selected_index = 0
        kb = KeyBindings()

        @kb.add('up')
        def _up(event: E) ->None:
            self._selected_index = max(0, self._selected_index - 1)

        @kb.add('down')
        def _down(event: E) ->None:
            self._selected_index = min(len(self.values) - 1, self.
                _selected_index + 1)

        @kb.add('pageup')
        def _pageup(event: E) ->None:
            w = event.app.layout.current_window
            if w.render_info:
                self._selected_index = max(0, self._selected_index - len(w.
                    render_info.displayed_lines))

        @kb.add('pagedown')
        def _pagedown(event: E) ->None:
            w = event.app.layout.current_window
            if w.render_info:
                self._selected_index = min(len(self.values) - 1, self.
                    _selected_index + len(w.render_info.displayed_lines))

        @kb.add('enter')
        @kb.add(' ')
        def _click(event: E) ->None:
            self._handle_enter()

        @kb.add(Keys.Any)
        def _find(event: E) ->None:
            values = list(self.values)
            for value in (values[self._selected_index + 1:] + values):
                text = fragment_list_to_text(to_formatted_text(value[1])
                    ).lower()
                if text.startswith(event.data.lower()):
                    self._selected_index = self.values.index(value)
                    return
        self.control = FormattedTextControl(self._get_text_fragments,
            key_bindings=kb, focusable=True)
        self.window = Window(content=self.control, style=self.
            container_style, right_margins=[ConditionalMargin(margin=
            ScrollbarMargin(display_arrows=True), filter=Condition(lambda :
            self.show_scrollbar))], dont_extend_height=True)

    def __pt_container__(self) ->Container:
        return self.window


class RadioList(_DialogList[_T]):
    """
    List of radio buttons. Only one can be checked at the same time.

    :param values: List of (value, label) tuples.
    """
    open_character = '('
    close_character = ')'
    container_style = 'class:radio-list'
    default_style = 'class:radio'
    selected_style = 'class:radio-selected'
    checked_style = 'class:radio-checked'
    multiple_selection = False

    def __init__(self, values: Sequence[tuple[_T, AnyFormattedText]],
        default: (_T | None)=None) ->None:
        if default is None:
            default_values = None
        else:
            default_values = [default]
        super().__init__(values, default_values=default_values)


class CheckboxList(_DialogList[_T]):
    """
    List of checkbox buttons. Several can be checked at the same time.

    :param values: List of (value, label) tuples.
    """
    open_character = '['
    close_character = ']'
    container_style = 'class:checkbox-list'
    default_style = 'class:checkbox'
    selected_style = 'class:checkbox-selected'
    checked_style = 'class:checkbox-checked'
    multiple_selection = True


class Checkbox(CheckboxList[str]):
    """Backward compatibility util: creates a 1-sized CheckboxList

    :param text: the text
    """
    show_scrollbar = False

    def __init__(self, text: AnyFormattedText='', checked: bool=False) ->None:
        values = [('value', text)]
        super().__init__(values=values)
        self.checked = checked


class VerticalLine:
    """
    A simple vertical line with a width of 1.
    """

    def __init__(self) ->None:
        self.window = Window(char=Border.VERTICAL, style=
            'class:line,vertical-line', width=1)

    def __pt_container__(self) ->Container:
        return self.window


class HorizontalLine:
    """
    A simple horizontal line with a height of 1.
    """

    def __init__(self) ->None:
        self.window = Window(char=Border.HORIZONTAL, style=
            'class:line,horizontal-line', height=1)

    def __pt_container__(self) ->Container:
        return self.window


class ProgressBar:

    def __init__(self) ->None:
        self._percentage = 60
        self.label = Label('60%')
        self.container = FloatContainer(content=Window(height=1), floats=[
            Float(content=self.label, top=0, bottom=0), Float(left=0, top=0,
            right=0, bottom=0, content=VSplit([Window(style=
            'class:progress-bar.used', width=lambda : D(weight=int(self.
            _percentage))), Window(style='class:progress-bar', width=lambda :
            D(weight=int(100 - self._percentage)))]))])

    def __pt_container__(self) ->Container:
        return self.container
