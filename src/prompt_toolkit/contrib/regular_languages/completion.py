"""
Completer for a regular grammar.
"""
from __future__ import annotations
from typing import Iterable
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from .compiler import Match, _CompiledGrammar
__all__ = ['GrammarCompleter']


class GrammarCompleter(Completer):
    """
    Completer which can be used for autocompletion according to variables in
    the grammar. Each variable can have a different autocompleter.

    :param compiled_grammar: `GrammarCompleter` instance.
    :param completers: `dict` mapping variable names of the grammar to the
                       `Completer` instances to be used for each variable.
    """

    def __init__(self, compiled_grammar: _CompiledGrammar, completers: dict
        [str, Completer]) ->None:
        self.compiled_grammar = compiled_grammar
        self.completers = completers

    def _get_completions_for_match(self, match: Match, complete_event:
        CompleteEvent) ->Iterable[Completion]:
        """
        Yield all the possible completions for this input string.
        (The completer assumes that the cursor position was at the end of the
        input string.)
        """
        pass

    def _remove_duplicates(self, items: Iterable[Completion]) ->list[Completion
        ]:
        """
        Remove duplicates, while keeping the order.
        (Sometimes we have duplicates, because the there several matches of the
        same grammar, each yielding similar completions.)
        """
        pass
