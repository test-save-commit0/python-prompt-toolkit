"""
Line editing functionality.
---------------------------

This provides a UI for a line input, similar to GNU Readline, libedit and
linenoise.

Either call the `prompt` function for every line input. Or create an instance
of the :class:`.PromptSession` class and call the `prompt` method from that
class. In the second case, we'll have a 'session' that keeps all the state like
the history in between several calls.

There is a lot of overlap between the arguments taken by the `prompt` function
and the `PromptSession` (like `completer`, `style`, etcetera). There we have
the freedom to decide which settings we want for the whole 'session', and which
we want for an individual `prompt`.

Example::

        # Simple `prompt` call.
        result = prompt('Say something: ')

        # Using a 'session'.
        s = PromptSession()
        result = s.prompt('Say something: ')
"""
from __future__ import annotations
from asyncio import get_running_loop
from contextlib import contextmanager
from enum import Enum
from functools import partial
from typing import TYPE_CHECKING, Callable, Generic, Iterator, TypeVar, Union, cast
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import AutoSuggest, DynamicAutoSuggest
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.clipboard import Clipboard, DynamicClipboard, InMemoryClipboard
from prompt_toolkit.completion import Completer, DynamicCompleter, ThreadedCompleter
from prompt_toolkit.cursor_shapes import AnyCursorShapeConfig, CursorShapeConfig, DynamicCursorShapeConfig
from prompt_toolkit.document import Document
from prompt_toolkit.enums import DEFAULT_BUFFER, SEARCH_BUFFER, EditingMode
from prompt_toolkit.eventloop import InputHook
from prompt_toolkit.filters import Condition, FilterOrBool, has_arg, has_focus, is_done, is_true, renderer_height_is_known, to_filter
from prompt_toolkit.formatted_text import AnyFormattedText, StyleAndTextTuples, fragment_list_to_text, merge_formatted_text, to_formatted_text
from prompt_toolkit.history import History, InMemoryHistory
from prompt_toolkit.input.base import Input
from prompt_toolkit.key_binding.bindings.auto_suggest import load_auto_suggest_bindings
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
from prompt_toolkit.key_binding.bindings.open_in_editor import load_open_in_editor_bindings
from prompt_toolkit.key_binding.key_bindings import ConditionalKeyBindings, DynamicKeyBindings, KeyBindings, KeyBindingsBase, merge_key_bindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Float, FloatContainer, HSplit, Window
from prompt_toolkit.layout.containers import ConditionalContainer, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl, SearchBufferControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.menus import CompletionsMenu, MultiColumnCompletionsMenu
from prompt_toolkit.layout.processors import AfterInput, AppendAutoSuggestion, ConditionalProcessor, DisplayMultipleCursors, DynamicProcessor, HighlightIncrementalSearchProcessor, HighlightSelectionProcessor, PasswordProcessor, Processor, ReverseSearchProcessor, merge_processors
from prompt_toolkit.layout.utils import explode_text_fragments
from prompt_toolkit.lexers import DynamicLexer, Lexer
from prompt_toolkit.output import ColorDepth, DummyOutput, Output
from prompt_toolkit.styles import BaseStyle, ConditionalStyleTransformation, DynamicStyle, DynamicStyleTransformation, StyleTransformation, SwapLightAndDarkStyleTransformation, merge_style_transformations
from prompt_toolkit.utils import get_cwidth, is_dumb_terminal, suspend_to_background_supported, to_str
from prompt_toolkit.validation import DynamicValidator, Validator
from prompt_toolkit.widgets.toolbars import SearchToolbar, SystemToolbar, ValidationToolbar
if TYPE_CHECKING:
    from prompt_toolkit.formatted_text.base import MagicFormattedText
__all__ = ['PromptSession', 'prompt', 'confirm', 'create_confirm_session',
    'CompleteStyle']
_StyleAndTextTuplesCallable = Callable[[], StyleAndTextTuples]
E = KeyPressEvent


def _split_multiline_prompt(get_prompt_text: _StyleAndTextTuplesCallable
    ) ->tuple[Callable[[], bool], _StyleAndTextTuplesCallable,
    _StyleAndTextTuplesCallable]:
    """
    Take a `get_prompt_text` function and return three new functions instead.
    One that tells whether this prompt consists of multiple lines; one that
    returns the fragments to be shown on the lines above the input; and another
    one with the fragments to be shown at the first line of the input.
    """
    pass


class _RPrompt(Window):
    """
    The prompt that is displayed on the right side of the Window.
    """

    def __init__(self, text: AnyFormattedText) ->None:
        super().__init__(FormattedTextControl(text=text), align=WindowAlign
            .RIGHT, style='class:rprompt')


class CompleteStyle(str, Enum):
    """
    How to display autocompletions for the prompt.
    """
    value: str
    COLUMN = 'COLUMN'
    MULTI_COLUMN = 'MULTI_COLUMN'
    READLINE_LIKE = 'READLINE_LIKE'


PromptContinuationText = Union[str, 'MagicFormattedText',
    StyleAndTextTuples, Callable[[int, int, int], AnyFormattedText]]
_T = TypeVar('_T')


class PromptSession(Generic[_T]):
    """
    PromptSession for a prompt application, which can be used as a GNU Readline
    replacement.

    This is a wrapper around a lot of ``prompt_toolkit`` functionality and can
    be a replacement for `raw_input`.

    All parameters that expect "formatted text" can take either just plain text
    (a unicode object), a list of ``(style_str, text)`` tuples or an HTML object.

    Example usage::

        s = PromptSession(message='>')
        text = s.prompt()

    :param message: Plain text or formatted text to be shown before the prompt.
        This can also be a callable that returns formatted text.
    :param multiline: `bool` or :class:`~prompt_toolkit.filters.Filter`.
        When True, prefer a layout that is more adapted for multiline input.
        Text after newlines is automatically indented, and search/arg input is
        shown below the input, instead of replacing the prompt.
    :param wrap_lines: `bool` or :class:`~prompt_toolkit.filters.Filter`.
        When True (the default), automatically wrap long lines instead of
        scrolling horizontally.
    :param is_password: Show asterisks instead of the actual typed characters.
    :param editing_mode: ``EditingMode.VI`` or ``EditingMode.EMACS``.
    :param vi_mode: `bool`, if True, Identical to ``editing_mode=EditingMode.VI``.
    :param complete_while_typing: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Enable autocompletion while
        typing.
    :param validate_while_typing: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Enable input validation while
        typing.
    :param enable_history_search: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Enable up-arrow parting
        string matching.
    :param search_ignore_case:
        :class:`~prompt_toolkit.filters.Filter`. Search case insensitive.
    :param lexer: :class:`~prompt_toolkit.lexers.Lexer` to be used for the
        syntax highlighting.
    :param validator: :class:`~prompt_toolkit.validation.Validator` instance
        for input validation.
    :param completer: :class:`~prompt_toolkit.completion.Completer` instance
        for input completion.
    :param complete_in_thread: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Run the completer code in a
        background thread in order to avoid blocking the user interface.
        For ``CompleteStyle.READLINE_LIKE``, this setting has no effect. There
        we always run the completions in the main thread.
    :param reserve_space_for_menu: Space to be reserved for displaying the menu.
        (0 means that no space needs to be reserved.)
    :param auto_suggest: :class:`~prompt_toolkit.auto_suggest.AutoSuggest`
        instance for input suggestions.
    :param style: :class:`.Style` instance for the color scheme.
    :param include_default_pygments_style: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Tell whether the default
        styling for Pygments lexers has to be included. By default, this is
        true, but it is recommended to be disabled if another Pygments style is
        passed as the `style` argument, otherwise, two Pygments styles will be
        merged.
    :param style_transformation:
        :class:`~prompt_toolkit.style.StyleTransformation` instance.
    :param swap_light_and_dark_colors: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. When enabled, apply
        :class:`~prompt_toolkit.style.SwapLightAndDarkStyleTransformation`.
        This is useful for switching between dark and light terminal
        backgrounds.
    :param enable_system_prompt: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Pressing Meta+'!' will show
        a system prompt.
    :param enable_suspend: `bool` or :class:`~prompt_toolkit.filters.Filter`.
        Enable Control-Z style suspension.
    :param enable_open_in_editor: `bool` or
        :class:`~prompt_toolkit.filters.Filter`. Pressing 'v' in Vi mode or
        C-X C-E in emacs mode will open an external editor.
    :param history: :class:`~prompt_toolkit.history.History` instance.
    :param clipboard: :class:`~prompt_toolkit.clipboard.Clipboard` instance.
        (e.g. :class:`~prompt_toolkit.clipboard.InMemoryClipboard`)
    :param rprompt: Text or formatted text to be displayed on the right side.
        This can also be a callable that returns (formatted) text.
    :param bottom_toolbar: Formatted text or callable which is supposed to
        return formatted text.
    :param prompt_continuation: Text that needs to be displayed for a multiline
        prompt continuation. This can either be formatted text or a callable
        that takes a `prompt_width`, `line_number` and `wrap_count` as input
        and returns formatted text. When this is `None` (the default), then
        `prompt_width` spaces will be used.
    :param complete_style: ``CompleteStyle.COLUMN``,
        ``CompleteStyle.MULTI_COLUMN`` or ``CompleteStyle.READLINE_LIKE``.
    :param mouse_support: `bool` or :class:`~prompt_toolkit.filters.Filter`
        to enable mouse support.
    :param placeholder: Text to be displayed when no input has been given
        yet. Unlike the `default` parameter, this won't be returned as part of
        the output ever. This can be formatted text or a callable that returns
        formatted text.
    :param refresh_interval: (number; in seconds) When given, refresh the UI
        every so many seconds.
    :param input: `Input` object. (Note that the preferred way to change the
        input/output is by creating an `AppSession`.)
    :param output: `Output` object.
    """
    _fields = ('message', 'lexer', 'completer', 'complete_in_thread',
        'is_password', 'editing_mode', 'key_bindings', 'is_password',
        'bottom_toolbar', 'style', 'style_transformation',
        'swap_light_and_dark_colors', 'color_depth', 'cursor',
        'include_default_pygments_style', 'rprompt', 'multiline',
        'prompt_continuation', 'wrap_lines', 'enable_history_search',
        'search_ignore_case', 'complete_while_typing',
        'validate_while_typing', 'complete_style', 'mouse_support',
        'auto_suggest', 'clipboard', 'validator', 'refresh_interval',
        'input_processors', 'placeholder', 'enable_system_prompt',
        'enable_suspend', 'enable_open_in_editor', 'reserve_space_for_menu',
        'tempfile_suffix', 'tempfile')

    def __init__(self, message: AnyFormattedText='', *, multiline:
        FilterOrBool=False, wrap_lines: FilterOrBool=True, is_password:
        FilterOrBool=False, vi_mode: bool=False, editing_mode: EditingMode=
        EditingMode.EMACS, complete_while_typing: FilterOrBool=True,
        validate_while_typing: FilterOrBool=True, enable_history_search:
        FilterOrBool=False, search_ignore_case: FilterOrBool=False, lexer:
        (Lexer | None)=None, enable_system_prompt: FilterOrBool=False,
        enable_suspend: FilterOrBool=False, enable_open_in_editor:
        FilterOrBool=False, validator: (Validator | None)=None, completer:
        (Completer | None)=None, complete_in_thread: bool=False,
        reserve_space_for_menu: int=8, complete_style: CompleteStyle=
        CompleteStyle.COLUMN, auto_suggest: (AutoSuggest | None)=None,
        style: (BaseStyle | None)=None, style_transformation: (
        StyleTransformation | None)=None, swap_light_and_dark_colors:
        FilterOrBool=False, color_depth: (ColorDepth | None)=None, cursor:
        AnyCursorShapeConfig=None, include_default_pygments_style:
        FilterOrBool=True, history: (History | None)=None, clipboard: (
        Clipboard | None)=None, prompt_continuation: (
        PromptContinuationText | None)=None, rprompt: AnyFormattedText=None,
        bottom_toolbar: AnyFormattedText=None, mouse_support: FilterOrBool=
        False, input_processors: (list[Processor] | None)=None, placeholder:
        (AnyFormattedText | None)=None, key_bindings: (KeyBindingsBase |
        None)=None, erase_when_done: bool=False, tempfile_suffix: (str |
        Callable[[], str] | None)='.txt', tempfile: (str | Callable[[], str
        ] | None)=None, refresh_interval: float=0, input: (Input | None)=
        None, output: (Output | None)=None) ->None:
        history = history or InMemoryHistory()
        clipboard = clipboard or InMemoryClipboard()
        if vi_mode:
            editing_mode = EditingMode.VI
        self._input = input
        self._output = output
        self.message = message
        self.lexer = lexer
        self.completer = completer
        self.complete_in_thread = complete_in_thread
        self.is_password = is_password
        self.key_bindings = key_bindings
        self.bottom_toolbar = bottom_toolbar
        self.style = style
        self.style_transformation = style_transformation
        self.swap_light_and_dark_colors = swap_light_and_dark_colors
        self.color_depth = color_depth
        self.cursor = cursor
        self.include_default_pygments_style = include_default_pygments_style
        self.rprompt = rprompt
        self.multiline = multiline
        self.prompt_continuation = prompt_continuation
        self.wrap_lines = wrap_lines
        self.enable_history_search = enable_history_search
        self.search_ignore_case = search_ignore_case
        self.complete_while_typing = complete_while_typing
        self.validate_while_typing = validate_while_typing
        self.complete_style = complete_style
        self.mouse_support = mouse_support
        self.auto_suggest = auto_suggest
        self.clipboard = clipboard
        self.validator = validator
        self.refresh_interval = refresh_interval
        self.input_processors = input_processors
        self.placeholder = placeholder
        self.enable_system_prompt = enable_system_prompt
        self.enable_suspend = enable_suspend
        self.enable_open_in_editor = enable_open_in_editor
        self.reserve_space_for_menu = reserve_space_for_menu
        self.tempfile_suffix = tempfile_suffix
        self.tempfile = tempfile
        self.history = history
        self.default_buffer = self._create_default_buffer()
        self.search_buffer = self._create_search_buffer()
        self.layout = self._create_layout()
        self.app = self._create_application(editing_mode, erase_when_done)

    def _dyncond(self, attr_name: str) ->Condition:
        """
        Dynamically take this setting from this 'PromptSession' class.
        `attr_name` represents an attribute name of this class. Its value
        can either be a boolean or a `Filter`.

        This returns something that can be used as either a `Filter`
        or `Filter`.
        """
        pass

    def _create_default_buffer(self) ->Buffer:
        """
        Create and return the default input buffer.
        """
        pass

    def _create_layout(self) ->Layout:
        """
        Create `Layout` for this prompt.
        """
        pass

    def _create_application(self, editing_mode: EditingMode,
        erase_when_done: bool) ->Application[_T]:
        """
        Create the `Application` object.
        """
        pass

    def _create_prompt_bindings(self) ->KeyBindings:
        """
        Create the KeyBindings for a prompt application.
        """
        pass

    def prompt(self, message: (AnyFormattedText | None)=None, *,
        editing_mode: (EditingMode | None)=None, refresh_interval: (float |
        None)=None, vi_mode: (bool | None)=None, lexer: (Lexer | None)=None,
        completer: (Completer | None)=None, complete_in_thread: (bool |
        None)=None, is_password: (bool | None)=None, key_bindings: (
        KeyBindingsBase | None)=None, bottom_toolbar: (AnyFormattedText |
        None)=None, style: (BaseStyle | None)=None, color_depth: (
        ColorDepth | None)=None, cursor: (AnyCursorShapeConfig | None)=None,
        include_default_pygments_style: (FilterOrBool | None)=None,
        style_transformation: (StyleTransformation | None)=None,
        swap_light_and_dark_colors: (FilterOrBool | None)=None, rprompt: (
        AnyFormattedText | None)=None, multiline: (FilterOrBool | None)=
        None, prompt_continuation: (PromptContinuationText | None)=None,
        wrap_lines: (FilterOrBool | None)=None, enable_history_search: (
        FilterOrBool | None)=None, search_ignore_case: (FilterOrBool | None
        )=None, complete_while_typing: (FilterOrBool | None)=None,
        validate_while_typing: (FilterOrBool | None)=None, complete_style:
        (CompleteStyle | None)=None, auto_suggest: (AutoSuggest | None)=
        None, validator: (Validator | None)=None, clipboard: (Clipboard |
        None)=None, mouse_support: (FilterOrBool | None)=None,
        input_processors: (list[Processor] | None)=None, placeholder: (
        AnyFormattedText | None)=None, reserve_space_for_menu: (int | None)
        =None, enable_system_prompt: (FilterOrBool | None)=None,
        enable_suspend: (FilterOrBool | None)=None, enable_open_in_editor:
        (FilterOrBool | None)=None, tempfile_suffix: (str | Callable[[],
        str] | None)=None, tempfile: (str | Callable[[], str] | None)=None,
        default: (str | Document)='', accept_default: bool=False, pre_run:
        (Callable[[], None] | None)=None, set_exception_handler: bool=True,
        handle_sigint: bool=True, in_thread: bool=False, inputhook: (
        InputHook | None)=None) ->_T:
        """
        Display the prompt.

        The first set of arguments is a subset of the :class:`~.PromptSession`
        class itself. For these, passing in ``None`` will keep the current
        values that are active in the session. Passing in a value will set the
        attribute for the session, which means that it applies to the current,
        but also to the next prompts.

        Note that in order to erase a ``Completer``, ``Validator`` or
        ``AutoSuggest``, you can't use ``None``. Instead pass in a
        ``DummyCompleter``, ``DummyValidator`` or ``DummyAutoSuggest`` instance
        respectively. For a ``Lexer`` you can pass in an empty ``SimpleLexer``.

        Additional arguments, specific for this prompt:

        :param default: The default input text to be shown. (This can be edited
            by the user).
        :param accept_default: When `True`, automatically accept the default
            value without allowing the user to edit the input.
        :param pre_run: Callable, called at the start of `Application.run`.
        :param in_thread: Run the prompt in a background thread; block the
            current thread. This avoids interference with an event loop in the
            current thread. Like `Application.run(in_thread=True)`.

        This method will raise ``KeyboardInterrupt`` when control-c has been
        pressed (for abort) and ``EOFError`` when control-d has been pressed
        (for exit).
        """
        pass

    @contextmanager
    def _dumb_prompt(self, message: AnyFormattedText='') ->Iterator[Application
        [_T]]:
        """
        Create prompt `Application` for prompt function for dumb terminals.

        Dumb terminals have minimum rendering capabilities. We can only print
        text to the screen. We can't use colors, and we can't do cursor
        movements. The Emacs inferior shell is an example of a dumb terminal.

        We will show the prompt, and wait for the input. We still handle arrow
        keys, and all custom key bindings, but we don't really render the
        cursor movements. Instead we only print the typed character that's
        right before the cursor.
        """
        pass

    def _get_continuation(self, width: int, line_number: int, wrap_count: int
        ) ->StyleAndTextTuples:
        """
        Insert the prompt continuation.

        :param width: The width that was used for the prompt. (more or less can
            be used.)
        :param line_number:
        :param wrap_count: Amount of times that the line has been wrapped.
        """
        pass

    def _get_line_prefix(self, line_number: int, wrap_count: int,
        get_prompt_text_2: _StyleAndTextTuplesCallable) ->StyleAndTextTuples:
        """
        Return whatever needs to be inserted before every line.
        (the prompt, or a line continuation.)
        """
        pass

    def _get_arg_text(self) ->StyleAndTextTuples:
        """'arg' toolbar, for in multiline mode."""
        pass

    def _inline_arg(self) ->StyleAndTextTuples:
        """'arg' prefix, for in single line mode."""
        pass


def prompt(message: (AnyFormattedText | None)=None, *, history: (History |
    None)=None, editing_mode: (EditingMode | None)=None, refresh_interval:
    (float | None)=None, vi_mode: (bool | None)=None, lexer: (Lexer | None)
    =None, completer: (Completer | None)=None, complete_in_thread: (bool |
    None)=None, is_password: (bool | None)=None, key_bindings: (
    KeyBindingsBase | None)=None, bottom_toolbar: (AnyFormattedText | None)
    =None, style: (BaseStyle | None)=None, color_depth: (ColorDepth | None)
    =None, cursor: AnyCursorShapeConfig=None,
    include_default_pygments_style: (FilterOrBool | None)=None,
    style_transformation: (StyleTransformation | None)=None,
    swap_light_and_dark_colors: (FilterOrBool | None)=None, rprompt: (
    AnyFormattedText | None)=None, multiline: (FilterOrBool | None)=None,
    prompt_continuation: (PromptContinuationText | None)=None, wrap_lines:
    (FilterOrBool | None)=None, enable_history_search: (FilterOrBool | None
    )=None, search_ignore_case: (FilterOrBool | None)=None,
    complete_while_typing: (FilterOrBool | None)=None,
    validate_while_typing: (FilterOrBool | None)=None, complete_style: (
    CompleteStyle | None)=None, auto_suggest: (AutoSuggest | None)=None,
    validator: (Validator | None)=None, clipboard: (Clipboard | None)=None,
    mouse_support: (FilterOrBool | None)=None, input_processors: (list[
    Processor] | None)=None, placeholder: (AnyFormattedText | None)=None,
    reserve_space_for_menu: (int | None)=None, enable_system_prompt: (
    FilterOrBool | None)=None, enable_suspend: (FilterOrBool | None)=None,
    enable_open_in_editor: (FilterOrBool | None)=None, tempfile_suffix: (
    str | Callable[[], str] | None)=None, tempfile: (str | Callable[[], str
    ] | None)=None, default: str='', accept_default: bool=False, pre_run: (
    Callable[[], None] | None)=None, set_exception_handler: bool=True,
    handle_sigint: bool=True, in_thread: bool=False, inputhook: (InputHook |
    None)=None) ->str:
    """
    The global `prompt` function. This will create a new `PromptSession`
    instance for every call.
    """
    pass


prompt.__doc__ = PromptSession.prompt.__doc__


def create_confirm_session(message: str, suffix: str=' (y/n) '
    ) ->PromptSession[bool]:
    """
    Create a `PromptSession` object for the 'confirm' function.
    """
    pass


def confirm(message: str='Confirm?', suffix: str=' (y/n) ') ->bool:
    """
    Display a confirmation prompt that returns True/False.
    """
    pass
