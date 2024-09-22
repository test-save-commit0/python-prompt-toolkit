from __future__ import annotations
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Tuple, Union, cast
from prompt_toolkit.mouse_events import MouseEvent
if TYPE_CHECKING:
    from typing_extensions import Protocol
    from prompt_toolkit.key_binding.key_bindings import NotImplementedOrNone
__all__ = ['OneStyleAndTextTuple', 'StyleAndTextTuples',
    'MagicFormattedText', 'AnyFormattedText', 'to_formatted_text',
    'is_formatted_text', 'Template', 'merge_formatted_text', 'FormattedText']
OneStyleAndTextTuple = Union[Tuple[str, str], Tuple[str, str, Callable[[
    MouseEvent], 'NotImplementedOrNone']]]
StyleAndTextTuples = List[OneStyleAndTextTuple]
if TYPE_CHECKING:
    from typing_extensions import TypeGuard


    class MagicFormattedText(Protocol):
        """
        Any object that implements ``__pt_formatted_text__`` represents formatted
        text.
        """

        def __pt_formatted_text__(self) ->StyleAndTextTuples:
            ...
AnyFormattedText = Union[str, 'MagicFormattedText', StyleAndTextTuples,
    Callable[[], Any], None]


def to_formatted_text(value: AnyFormattedText, style: str='', auto_convert:
    bool=False) ->FormattedText:
    """
    Convert the given value (which can be formatted text) into a list of text
    fragments. (Which is the canonical form of formatted text.) The outcome is
    always a `FormattedText` instance, which is a list of (style, text) tuples.

    It can take a plain text string, an `HTML` or `ANSI` object, anything that
    implements `__pt_formatted_text__` or a callable that takes no arguments and
    returns one of those.

    :param style: An additional style string which is applied to all text
        fragments.
    :param auto_convert: If `True`, also accept other types, and convert them
        to a string first.
    """
    pass


def is_formatted_text(value: object) ->TypeGuard[AnyFormattedText]:
    """
    Check whether the input is valid formatted text (for use in assert
    statements).
    In case of a callable, it doesn't check the return type.
    """
    pass


class FormattedText(StyleAndTextTuples):
    """
    A list of ``(style, text)`` tuples.

    (In some situations, this can also be ``(style, text, mouse_handler)``
    tuples.)
    """

    def __pt_formatted_text__(self) ->StyleAndTextTuples:
        return self

    def __repr__(self) ->str:
        return 'FormattedText(%s)' % super().__repr__()


class Template:
    """
    Template for string interpolation with formatted text.

    Example::

        Template(' ... {} ... ').format(HTML(...))

    :param text: Plain text.
    """

    def __init__(self, text: str) ->None:
        assert '{0}' not in text
        self.text = text


def merge_formatted_text(items: Iterable[AnyFormattedText]) ->AnyFormattedText:
    """
    Merge (Concatenate) several pieces of formatted text together.
    """
    pass
