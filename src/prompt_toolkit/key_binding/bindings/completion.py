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
    pass


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
    pass


def _display_completions_like_readline(app: Application[object],
    completions: list[Completion]) ->asyncio.Task[None]:
    """
    Display the list of completions in columns above the prompt.
    This will ask for a confirmation if there are too many completions to fit
    on a single page and provide a paginator to walk through them.
    """
    pass


def _create_more_session(message: str='--MORE--') ->PromptSession[bool]:
    """
    Create a `PromptSession` object for displaying the "--MORE--".
    """
    pass
