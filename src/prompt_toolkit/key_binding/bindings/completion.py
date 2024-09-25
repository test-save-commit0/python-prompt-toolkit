"""
Key binding handlers for displaying completions.
"""
from __future__ import annotations
import asyncio
import math
from typing import TYPE_CHECKING
from prompt_toolkit.application.run_in_terminal import in_terminal
from prompt_toolkit.completion import CompleteEvent, Completion, get_common_complete_suffix
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.utils import get_cwidth
if TYPE_CHECKING:
    from prompt_toolkit.application import Application
    from prompt_toolkit.shortcuts import PromptSession
__all__ = ['generate_completions', 'display_completions_like_readline']
E = KeyPressEvent


def generate_completions(event: E) ->None:
    """
    Tab-completion: where the first tab completes the common suffix and the
    second tab lists all the completions.
    """
    b = event.current_buffer

    # If we are at the end of the input, and there's no selection, then we can
    # safely insert the common suffix, otherwise, only list the completions.
    if b.cursor_position == len(b.text) and not b.selection_state:
        completions = list(b.completer.get_completions(b.document, CompleteEvent()))
        if completions:
            common_suffix = get_common_complete_suffix(b.document, completions)
            if common_suffix:
                b.insert_text(common_suffix)
            else:
                b.start_completion(select_first=False)
    else:
        b.start_completion(select_first=False)


def display_completions_like_readline(event: E) ->None:
    """
    Key binding handler for readline-style tab completion.
    This is meant to be as similar as possible to the way how readline displays
    completions.

    Generate the completions immediately (blocking) and display them above the
    prompt in columns.

    Usage::

        # Call this handler when 'Tab' has been pressed.
        key_bindings.add(Keys.ControlI)(display_completions_like_readline)
    """
    b = event.current_buffer
    completions = list(b.completer.get_completions(b.document, CompleteEvent()))

    if completions:
        asyncio.ensure_future(_display_completions_like_readline(event.app, completions))


def _display_completions_like_readline(app: Application[object],
    completions: list[Completion]) ->asyncio.Task[None]:
    """
    Display the list of completions in columns above the prompt.
    This will ask for a confirmation if there are too many completions to fit
    on a single page and provide a paginator to walk through them.
    """
    async def run():
        loop = asyncio.get_event_loop()
        term_size = app.output.get_size()
        page_size = term_size.rows - 1  # Leave one row for the prompt
        completions_per_page = page_size * (term_size.columns // 20)
        pages = math.ceil(len(completions) / completions_per_page)

        if pages > 1:
            show_meta = await loop.run_in_executor(None, _create_more_session().prompt)
            if not show_meta:
                return

        def format_completion(completion: Completion) -> StyleAndTextTuples:
            return [('class:completion', completion.text)]

        for page in range(pages):
            start = page * completions_per_page
            end = min((page + 1) * completions_per_page, len(completions))
            page_completions = completions[start:end]

            formatted_completions = [format_completion(c) for c in page_completions]
            if page < pages - 1:
                formatted_completions.append([('class:completion', '--MORE--')])

            with in_terminal():
                app.print_formatted_text(formatted_completions, style='class:completion-menu')

            if page < pages - 1:
                show_next = await loop.run_in_executor(None, _create_more_session().prompt)
                if not show_next:
                    break

    return asyncio.create_task(run())


def _create_more_session(message: str='--MORE--') ->PromptSession[bool]:
    """
    Create a `PromptSession` object for displaying the "--MORE--".
    """
    from prompt_toolkit.shortcuts import PromptSession

    bindings = KeyBindings()

    @bindings.add(' ')
    @bindings.add('y')
    @bindings.add('Y')
    @bindings.add(Keys.Enter)
    @bindings.add(Keys.ControlJ)
    def _(event):
        event.app.exit(result=True)

    @bindings.add('n')
    @bindings.add('N')
    @bindings.add('q')
    @bindings.add('Q')
    @bindings.add(Keys.ControlC)
    def _(event):
        event.app.exit(result=False)

    @bindings.add(Keys.Any)
    def _(event):
        " Disable inserting of text. "

    return PromptSession(
        message,
        key_bindings=bindings,
        erase_when_done=True,
    )
