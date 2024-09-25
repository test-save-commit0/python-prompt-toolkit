from __future__ import annotations
from typing import Any
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.enums import SYSTEM_BUFFER
from prompt_toolkit.filters import Condition, FilterOrBool, emacs_mode, has_arg, has_completions, has_focus, has_validation_error, to_filter, vi_mode, vi_navigation_mode
from prompt_toolkit.formatted_text import AnyFormattedText, StyleAndTextTuples, fragment_list_len, to_formatted_text
from prompt_toolkit.key_binding.key_bindings import ConditionalKeyBindings, KeyBindings, KeyBindingsBase, merge_key_bindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import ConditionalContainer, Container, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl, SearchBufferControl, UIContent, UIControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.search import SearchDirection
__all__ = ['ArgToolbar', 'CompletionsToolbar', 'FormattedTextToolbar',
    'SearchToolbar', 'SystemToolbar', 'ValidationToolbar']
E = KeyPressEvent


class FormattedTextToolbar(Window):

    def __init__(self, text: AnyFormattedText, style: str='', **kw: Any
        ) ->None:
        super().__init__(FormattedTextControl(text, **kw), style=style,
            dont_extend_height=True, height=Dimension(min=1))


class SystemToolbar:
    """
    Toolbar for a system prompt.

    :param prompt: Prompt to be displayed to the user.
    """

    def __init__(self, prompt: AnyFormattedText='Shell command: ',
        enable_global_bindings: FilterOrBool=True) ->None:
        self.prompt = prompt
        self.enable_global_bindings = to_filter(enable_global_bindings)
        self.system_buffer = Buffer(name=SYSTEM_BUFFER)
        self._bindings = self._build_key_bindings()
        self.buffer_control = BufferControl(buffer=self.system_buffer,
            lexer=SimpleLexer(style='class:system-toolbar.text'),
            input_processors=[BeforeInput(lambda : self.prompt, style=
            'class:system-toolbar')], key_bindings=self._bindings)
        self.window = Window(self.buffer_control, height=1, style=
            'class:system-toolbar')
        self.container = ConditionalContainer(content=self.window, filter=
            has_focus(self.system_buffer))

    def __pt_container__(self) ->Container:
        return self.container


class ArgToolbar:

    def __init__(self) ->None:

        def get_formatted_text() ->StyleAndTextTuples:
            arg = get_app().key_processor.arg or ''
            if arg == '-':
                arg = '-1'
            return [('class:arg-toolbar', 'Repeat: '), (
                'class:arg-toolbar.text', arg)]
        self.window = Window(FormattedTextControl(get_formatted_text), height=1
            )
        self.container = ConditionalContainer(content=self.window, filter=
            has_arg)

    def __pt_container__(self) ->Container:
        return self.container


class SearchToolbar:
    """
    :param vi_mode: Display '/' and '?' instead of I-search.
    :param ignore_case: Search case insensitive.
    """

    def __init__(self, search_buffer: (Buffer | None)=None, vi_mode: bool=
        False, text_if_not_searching: AnyFormattedText='',
        forward_search_prompt: AnyFormattedText='I-search: ',
        backward_search_prompt: AnyFormattedText='I-search backward: ',
        ignore_case: FilterOrBool=False) ->None:
        if search_buffer is None:
            search_buffer = Buffer()

        @Condition
        def is_searching() ->bool:
            return self.control in get_app().layout.search_links

        def get_before_input() ->AnyFormattedText:
            if not is_searching():
                return text_if_not_searching
            elif self.control.searcher_search_state.direction == SearchDirection.BACKWARD:
                return '?' if vi_mode else backward_search_prompt
            else:
                return '/' if vi_mode else forward_search_prompt
        self.search_buffer = search_buffer
        self.control = SearchBufferControl(buffer=search_buffer,
            input_processors=[BeforeInput(get_before_input, style=
            'class:search-toolbar.prompt')], lexer=SimpleLexer(style=
            'class:search-toolbar.text'), ignore_case=ignore_case)
        self.container = ConditionalContainer(content=Window(self.control,
            height=1, style='class:search-toolbar'), filter=is_searching)

    def __pt_container__(self) ->Container:
        return self.container


class _CompletionsToolbarControl(UIControl):
    def create_content(self, width: int, height: int) -> UIContent:
        """Create the content for the completions toolbar."""
        app = get_app()
        if app.current_buffer.complete_state:
            completions = app.current_buffer.complete_state.current_completions
            index = app.current_buffer.complete_state.complete_index

            # Format completions
            formatted_completions = []
            for i, completion in enumerate(completions):
                if i == index:
                    formatted_completions.append(('class:completion-toolbar.completion.current', completion.display))
                else:
                    formatted_completions.append(('class:completion-toolbar.completion', completion.display))
                
                if i < len(completions) - 1:
                    formatted_completions.append(('class:completion-toolbar.arrow', ' > '))

            return UIContent(
                lambda i: formatted_completions,
                line_count=1,
                show_cursor=False
            )
        else:
            return UIContent(lambda i: [], line_count=1)

    def is_focusable(self) -> bool:
        return False


class CompletionsToolbar:

    def __init__(self) -> None:
        self.control = _CompletionsToolbarControl()
        self.container = ConditionalContainer(
            content=Window(
                self.control,
                height=1,
                style='class:completion-toolbar'
            ),
            filter=has_completions
        )

    def __pt_container__(self) -> Container:
        return self.container


class ValidationToolbar:

    def __init__(self, show_position: bool=False) ->None:

        def get_formatted_text() ->StyleAndTextTuples:
            buff = get_app().current_buffer
            if buff.validation_error:
                row, column = buff.document.translate_index_to_position(buff
                    .validation_error.cursor_position)
                if show_position:
                    text = '{} (line={} column={})'.format(buff.
                        validation_error.message, row + 1, column + 1)
                else:
                    text = buff.validation_error.message
                return [('class:validation-toolbar', text)]
            else:
                return []
        self.control = FormattedTextControl(get_formatted_text)
        self.container = ConditionalContainer(content=Window(self.control,
            height=1), filter=has_validation_error)

    def __pt_container__(self) ->Container:
        return self.container
