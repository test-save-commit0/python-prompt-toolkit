"""
Parser for VT100 input stream.
"""
from __future__ import annotations
import re
from typing import Callable, Dict, Generator
from ..key_binding.key_processor import KeyPress
from ..keys import Keys
from .ansi_escape_sequences import ANSI_SEQUENCES
__all__ = ['Vt100Parser']
_cpr_response_re = re.compile('^' + re.escape('\x1b[') + '\\d+;\\d+R\\Z')
_mouse_event_re = re.compile('^' + re.escape('\x1b[') +
    '(<?[\\d;]+[mM]|M...)\\Z')
_cpr_response_prefix_re = re.compile('^' + re.escape('\x1b[') + '[\\d;]*\\Z')
_mouse_event_prefix_re = re.compile('^' + re.escape('\x1b[') +
    '(<?[\\d;]*|M.{0,2})\\Z')


class _Flush:
    """Helper object to indicate flush operation to the parser."""
    pass


class _IsPrefixOfLongerMatchCache(Dict[str, bool]):
    """
    Dictionary that maps input sequences to a boolean indicating whether there is
    any key that start with this characters.
    """

    def __missing__(self, prefix: str) ->bool:
        if _cpr_response_prefix_re.match(prefix
            ) or _mouse_event_prefix_re.match(prefix):
            result = True
        else:
            result = any(v for k, v in ANSI_SEQUENCES.items() if k.
                startswith(prefix) and k != prefix)
        self[prefix] = result
        return result


_IS_PREFIX_OF_LONGER_MATCH_CACHE = _IsPrefixOfLongerMatchCache()


class Vt100Parser:
    """
    Parser for VT100 input stream.
    Data can be fed through the `feed` method and the given callback will be
    called with KeyPress objects.

    ::

        def callback(key):
            pass
        i = Vt100Parser(callback)
        i.feed('data...')

    :attr feed_key_callback: Function that will be called when a key is parsed.
    """

    def __init__(self, feed_key_callback: Callable[[KeyPress], None]) ->None:
        self.feed_key_callback = feed_key_callback
        self.reset()

    def _start_parser(self) ->None:
        """
        Start the parser coroutine.
        """
        self._input_parser = self._input_parser_generator()
        next(self._input_parser)

    def _get_match(self, prefix: str) ->(None | Keys | tuple[Keys, ...]):
        """
        Return the key (or keys) that maps to this prefix.
        """
        if prefix in ANSI_SEQUENCES:
            return ANSI_SEQUENCES[prefix]
        elif _cpr_response_re.match(prefix):
            return Keys.CPRResponse
        elif _mouse_event_re.match(prefix):
            return Keys.Vt100MouseEvent
        return None

    def _input_parser_generator(self) ->Generator[None, str | _Flush, None]:
        """
        Coroutine (state machine) for the input parser.
        """
        prefix = ''
        retry = False
        flush = False

        while True:
            flush = False
            retry = False

            if retry:
                data = prefix
            else:
                data = yield

            if isinstance(data, _Flush):
                flush = True
                data = ''

            for c in data:
                prefix += c
                is_prefix_of_longer_match = _IS_PREFIX_OF_LONGER_MATCH_CACHE[prefix]
                match = self._get_match(prefix)

                if is_prefix_of_longer_match and not flush:
                    # No exact match found, but it is a prefix of a longer match.
                    continue

                elif match is None:
                    # No match and also not a prefix of a longer match.
                    # Reset prefix and retry with the next character.
                    self._call_handler(prefix[0], '')
                    prefix = prefix[1:]
                    retry = True
                    break

                else:
                    # Match found.
                    self._call_handler(match, '')
                    prefix = ''
                    retry = False

            if flush and prefix:
                # Flush prefix.
                self._call_handler(prefix, '')
                prefix = ''

    def _call_handler(self, key: (str | Keys | tuple[Keys, ...]),
        insert_text: str) ->None:
        """
        Callback to handler.
        """
        if isinstance(key, tuple):
            for k in key:
                self._call_handler(k, insert_text)
        else:
            if insert_text:
                self.feed_key_callback(KeyPress(key, insert_text))
            else:
                self.feed_key_callback(KeyPress(key))

    def feed(self, data: str) ->None:
        """
        Feed the input stream.

        :param data: Input string (unicode).
        """
        self._input_parser.send(data)

    def flush(self) ->None:
        """
        Flush the buffer of the input stream.

        This will allow us to handle the escape key (or maybe meta) sooner.
        The input received by the escape key is actually the same as the first
        characters of e.g. Arrow-Up, so without knowing what follows the escape
        sequence, we don't know whether escape has been pressed, or whether
        it's something else. This flush function should be called after a
        timeout, and processes everything that's still in the buffer as-is, so
        without assuming any characters will follow.
        """
        self._input_parser.send(_Flush())

    def feed_and_flush(self, data: str) ->None:
        """
        Wrapper around ``feed`` and ``flush``.
        """
        self.feed(data)
        self.flush()
