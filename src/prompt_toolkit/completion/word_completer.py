from __future__ import annotations
from typing import Callable, Iterable, Mapping, Pattern
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import AnyFormattedText
__all__ = ['WordCompleter']


class WordCompleter(Completer):
    """
    Simple autocompletion on a list of words.

    :param words: List of words or callable that returns a list of words.
    :param ignore_case: If True, case-insensitive completion.
    :param meta_dict: Optional dict mapping words to their meta-text. (This
        should map strings to strings or formatted text.)
    :param WORD: When True, use WORD characters.
    :param sentence: When True, don't complete by comparing the word before the
        cursor, but by comparing all the text before the cursor. In this case,
        the list of words is just a list of strings, where each string can
        contain spaces. (Can not be used together with the WORD option.)
    :param match_middle: When True, match not only the start, but also in the
                         middle of the word.
    :param pattern: Optional compiled regex for finding the word before
        the cursor to complete. When given, use this regex pattern instead of
        default one (see document._FIND_WORD_RE)
    """

    def __init__(self, words: (list[str] | Callable[[], list[str]]),
        ignore_case: bool=False, display_dict: (Mapping[str,
        AnyFormattedText] | None)=None, meta_dict: (Mapping[str,
        AnyFormattedText] | None)=None, WORD: bool=False, sentence: bool=
        False, match_middle: bool=False, pattern: (Pattern[str] | None)=None
        ) ->None:
        assert not (WORD and sentence)
        self.words = words
        self.ignore_case = ignore_case
        self.display_dict = display_dict or {}
        self.meta_dict = meta_dict or {}
        self.WORD = WORD
        self.sentence = sentence
        self.match_middle = match_middle
        self.pattern = pattern
