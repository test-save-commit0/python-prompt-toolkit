"""
Validator for a regular language.
"""
from __future__ import annotations
from prompt_toolkit.document import Document
from prompt_toolkit.validation import ValidationError, Validator
from .compiler import _CompiledGrammar
__all__ = ['GrammarValidator']


class GrammarValidator(Validator):
    """
    Validator which can be used for validation according to variables in
    the grammar. Each variable can have its own validator.

    :param compiled_grammar: `GrammarCompleter` instance.
    :param validators: `dict` mapping variable names of the grammar to the
                       `Validator` instances to be used for each variable.
    """

    def __init__(self, compiled_grammar: _CompiledGrammar, validators: dict
        [str, Validator]) ->None:
        self.compiled_grammar = compiled_grammar
        self.validators = validators
