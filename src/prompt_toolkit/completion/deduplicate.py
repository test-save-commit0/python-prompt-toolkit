from __future__ import annotations
from typing import Iterable
from prompt_toolkit.document import Document
from .base import CompleteEvent, Completer, Completion
__all__ = ['DeduplicateCompleter']


class DeduplicateCompleter(Completer):
    """
    Wrapper around a completer that removes duplicates. Only the first unique
    completions are kept.

    Completions are considered to be a duplicate if they result in the same
    document text when they would be applied.
    """

    def __init__(self, completer: Completer) ->None:
        self.completer = completer
