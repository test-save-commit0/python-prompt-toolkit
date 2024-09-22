"""
`Fish-style <http://fishshell.com/>`_  like auto-suggestion.

While a user types input in a certain buffer, suggestions are generated
(asynchronously.) Usually, they are displayed after the input. When the cursor
presses the right arrow and the cursor is at the end of the input, the
suggestion will be inserted.

If you want the auto suggestions to be asynchronous (in a background thread),
because they take too much time, and could potentially block the event loop,
then wrap the :class:`.AutoSuggest` instance into a
:class:`.ThreadedAutoSuggest`.
"""
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Callable
from prompt_toolkit.eventloop import run_in_executor_with_context
from .document import Document
from .filters import Filter, to_filter
if TYPE_CHECKING:
    from .buffer import Buffer
__all__ = ['Suggestion', 'AutoSuggest', 'ThreadedAutoSuggest',
    'DummyAutoSuggest', 'AutoSuggestFromHistory', 'ConditionalAutoSuggest',
    'DynamicAutoSuggest']


class Suggestion:
    """
    Suggestion returned by an auto-suggest algorithm.

    :param text: The suggestion text.
    """

    def __init__(self, text: str) ->None:
        self.text = text

    def __repr__(self) ->str:
        return 'Suggestion(%s)' % self.text


class AutoSuggest(metaclass=ABCMeta):
    """
    Base class for auto suggestion implementations.
    """

    @abstractmethod
    def get_suggestion(self, buffer: Buffer, document: Document) ->(Suggestion
         | None):
        """
        Return `None` or a :class:`.Suggestion` instance.

        We receive both :class:`~prompt_toolkit.buffer.Buffer` and
        :class:`~prompt_toolkit.document.Document`. The reason is that auto
        suggestions are retrieved asynchronously. (Like completions.) The
        buffer text could be changed in the meantime, but ``document`` contains
        the buffer document like it was at the start of the auto suggestion
        call. So, from here, don't access ``buffer.text``, but use
        ``document.text`` instead.

        :param buffer: The :class:`~prompt_toolkit.buffer.Buffer` instance.
        :param document: The :class:`~prompt_toolkit.document.Document` instance.
        """
        pass

    async def get_suggestion_async(self, buff: Buffer, document: Document) ->(
        Suggestion | None):
        """
        Return a :class:`.Future` which is set when the suggestions are ready.
        This function can be overloaded in order to provide an asynchronous
        implementation.
        """
        pass


class ThreadedAutoSuggest(AutoSuggest):
    """
    Wrapper that runs auto suggestions in a thread.
    (Use this to prevent the user interface from becoming unresponsive if the
    generation of suggestions takes too much time.)
    """

    def __init__(self, auto_suggest: AutoSuggest) ->None:
        self.auto_suggest = auto_suggest

    async def get_suggestion_async(self, buff: Buffer, document: Document) ->(
        Suggestion | None):
        """
        Run the `get_suggestion` function in a thread.
        """
        pass


class DummyAutoSuggest(AutoSuggest):
    """
    AutoSuggest class that doesn't return any suggestion.
    """


class AutoSuggestFromHistory(AutoSuggest):
    """
    Give suggestions based on the lines in the history.
    """


class ConditionalAutoSuggest(AutoSuggest):
    """
    Auto suggest that can be turned on and of according to a certain condition.
    """

    def __init__(self, auto_suggest: AutoSuggest, filter: (bool | Filter)
        ) ->None:
        self.auto_suggest = auto_suggest
        self.filter = to_filter(filter)


class DynamicAutoSuggest(AutoSuggest):
    """
    Validator class that can dynamically returns any Validator.

    :param get_validator: Callable that returns a :class:`.Validator` instance.
    """

    def __init__(self, get_auto_suggest: Callable[[], AutoSuggest | None]
        ) ->None:
        self.get_auto_suggest = get_auto_suggest
