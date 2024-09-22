"""
`GrammarLexer` is compatible with other lexers and can be used to highlight
the input using a regular grammar with annotations.
"""
from __future__ import annotations
from typing import Callable
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text.base import StyleAndTextTuples
from prompt_toolkit.formatted_text.utils import split_lines
from prompt_toolkit.lexers import Lexer
from .compiler import _CompiledGrammar
__all__ = ['GrammarLexer']


class GrammarLexer(Lexer):
    """
    Lexer which can be used for highlighting of fragments according to variables in the grammar.

    (It does not actual lexing of the string, but it exposes an API, compatible
    with the Pygments lexer class.)

    :param compiled_grammar: Grammar as returned by the `compile()` function.
    :param lexers: Dictionary mapping variable names of the regular grammar to
                   the lexers that should be used for this part. (This can
                   call other lexers recursively.) If you wish a part of the
                   grammar to just get one fragment, use a
                   `prompt_toolkit.lexers.SimpleLexer`.
    """

    def __init__(self, compiled_grammar: _CompiledGrammar, default_style:
        str='', lexers: (dict[str, Lexer] | None)=None) ->None:
        self.compiled_grammar = compiled_grammar
        self.default_style = default_style
        self.lexers = lexers or {}
