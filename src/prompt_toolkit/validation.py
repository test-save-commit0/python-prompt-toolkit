"""
Input validation for a `Buffer`.
(Validators will be called before accepting input.)
"""
from __future__ import annotations
from abc import ABCMeta, abstractmethod
from typing import Callable
from prompt_toolkit.eventloop import run_in_executor_with_context
from .document import Document
from .filters import FilterOrBool, to_filter
__all__ = ['ConditionalValidator', 'ValidationError', 'Validator',
    'ThreadedValidator', 'DummyValidator', 'DynamicValidator']


class ValidationError(Exception):
    """
    Error raised by :meth:`.Validator.validate`.

    :param cursor_position: The cursor position where the error occurred.
    :param message: Text.
    """

    def __init__(self, cursor_position: int=0, message: str='') ->None:
        super().__init__(message)
        self.cursor_position = cursor_position
        self.message = message

    def __repr__(self) ->str:
        return '{}(cursor_position={!r}, message={!r})'.format(self.
            __class__.__name__, self.cursor_position, self.message)


class Validator(metaclass=ABCMeta):
    """
    Abstract base class for an input validator.

    A validator is typically created in one of the following two ways:

    - Either by overriding this class and implementing the `validate` method.
    - Or by passing a callable to `Validator.from_callable`.

    If the validation takes some time and needs to happen in a background
    thread, this can be wrapped in a :class:`.ThreadedValidator`.
    """

    @abstractmethod
    def validate(self, document: Document) ->None:
        """
        Validate the input.
        If invalid, this should raise a :class:`.ValidationError`.

        :param document: :class:`~prompt_toolkit.document.Document` instance.
        """
        pass

    async def validate_async(self, document: Document) ->None:
        """
        Return a `Future` which is set when the validation is ready.
        This function can be overloaded in order to provide an asynchronous
        implementation.
        """
        pass

    @classmethod
    def from_callable(cls, validate_func: Callable[[str], bool],
        error_message: str='Invalid input', move_cursor_to_end: bool=False
        ) ->Validator:
        """
        Create a validator from a simple validate callable. E.g.:

        .. code:: python

            def is_valid(text):
                return text in ['hello', 'world']
            Validator.from_callable(is_valid, error_message='Invalid input')

        :param validate_func: Callable that takes the input string, and returns
            `True` if the input is valid input.
        :param error_message: Message to be displayed if the input is invalid.
        :param move_cursor_to_end: Move the cursor to the end of the input, if
            the input is invalid.
        """
        pass


class _ValidatorFromCallable(Validator):
    """
    Validate input from a simple callable.
    """

    def __init__(self, func: Callable[[str], bool], error_message: str,
        move_cursor_to_end: bool) ->None:
        self.func = func
        self.error_message = error_message
        self.move_cursor_to_end = move_cursor_to_end

    def __repr__(self) ->str:
        return f'Validator.from_callable({self.func!r})'


class ThreadedValidator(Validator):
    """
    Wrapper that runs input validation in a thread.
    (Use this to prevent the user interface from becoming unresponsive if the
    input validation takes too much time.)
    """

    def __init__(self, validator: Validator) ->None:
        self.validator = validator

    async def validate_async(self, document: Document) ->None:
        """
        Run the `validate` function in a thread.
        """
        pass


class DummyValidator(Validator):
    """
    Validator class that accepts any input.
    """


class ConditionalValidator(Validator):
    """
    Validator that can be switched on/off according to
    a filter. (This wraps around another validator.)
    """

    def __init__(self, validator: Validator, filter: FilterOrBool) ->None:
        self.validator = validator
        self.filter = to_filter(filter)


class DynamicValidator(Validator):
    """
    Validator class that can dynamically returns any Validator.

    :param get_validator: Callable that returns a :class:`.Validator` instance.
    """

    def __init__(self, get_validator: Callable[[], Validator | None]) ->None:
        self.get_validator = get_validator
