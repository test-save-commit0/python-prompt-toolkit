"""
Key bindings registry.

A `KeyBindings` object is a container that holds a list of key bindings. It has a
very efficient internal data structure for checking which key bindings apply
for a pressed key.

Typical usage::

    kb = KeyBindings()

    @kb.add(Keys.ControlX, Keys.ControlC, filter=INSERT)
    def handler(event):
        # Handle ControlX-ControlC key sequence.
        pass

It is also possible to combine multiple KeyBindings objects. We do this in the
default key bindings. There are some KeyBindings objects that contain the Emacs
bindings, while others contain the Vi bindings. They are merged together using
`merge_key_bindings`.

We also have a `ConditionalKeyBindings` object that can enable/disable a group of
key bindings at once.


It is also possible to add a filter to a function, before a key binding has
been assigned, through the `key_binding` decorator.::

    # First define a key handler with the `filter`.
    @key_binding(filter=condition)
    def my_key_binding(event):
        ...

    # Later, add it to the key bindings.
    kb.add(Keys.A, my_key_binding)
"""
from __future__ import annotations
from abc import ABCMeta, abstractmethod, abstractproperty
from inspect import isawaitable
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Hashable, Sequence, Tuple, TypeVar, Union, cast
from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.filters import FilterOrBool, Never, to_filter
from prompt_toolkit.keys import KEY_ALIASES, Keys
if TYPE_CHECKING:
    from .key_processor import KeyPressEvent
    NotImplementedOrNone = object
__all__ = ['NotImplementedOrNone', 'Binding', 'KeyBindingsBase',
    'KeyBindings', 'ConditionalKeyBindings', 'merge_key_bindings',
    'DynamicKeyBindings', 'GlobalOnlyKeyBindings']
KeyHandlerCallable = Callable[['KeyPressEvent'], Union[
    'NotImplementedOrNone', Coroutine[Any, Any, 'NotImplementedOrNone']]]


class Binding:
    """
    Key binding: (key sequence + handler + filter).
    (Immutable binding class.)

    :param record_in_macro: When True, don't record this key binding when a
        macro is recorded.
    """

    def __init__(self, keys: tuple[Keys | str, ...], handler:
        KeyHandlerCallable, filter: FilterOrBool=True, eager: FilterOrBool=
        False, is_global: FilterOrBool=False, save_before: Callable[[
        KeyPressEvent], bool]=lambda e: True, record_in_macro: FilterOrBool
        =True) ->None:
        self.keys = keys
        self.handler = handler
        self.filter = to_filter(filter)
        self.eager = to_filter(eager)
        self.is_global = to_filter(is_global)
        self.save_before = save_before
        self.record_in_macro = to_filter(record_in_macro)

    def __repr__(self) ->str:
        return '{}(keys={!r}, handler={!r})'.format(self.__class__.__name__,
            self.keys, self.handler)


KeysTuple = Tuple[Union[Keys, str], ...]


class KeyBindingsBase(metaclass=ABCMeta):
    """
    Interface for a KeyBindings.
    """

    @abstractproperty
    def _version(self) ->Hashable:
        """
        For cache invalidation. - This should increase every time that
        something changes.
        """
        pass

    @abstractmethod
    def get_bindings_for_keys(self, keys: KeysTuple) ->list[Binding]:
        """
        Return a list of key bindings that can handle these keys.
        (This return also inactive bindings, so the `filter` still has to be
        called, for checking it.)

        :param keys: tuple of keys.
        """
        pass

    @abstractmethod
    def get_bindings_starting_with_keys(self, keys: KeysTuple) ->list[Binding]:
        """
        Return a list of key bindings that handle a key sequence starting with
        `keys`. (It does only return bindings for which the sequences are
        longer than `keys`. And like `get_bindings_for_keys`, it also includes
        inactive bindings.)

        :param keys: tuple of keys.
        """
        pass

    @abstractproperty
    def bindings(self) ->list[Binding]:
        """
        List of `Binding` objects.
        (These need to be exposed, so that `KeyBindings` objects can be merged
        together.)
        """
        pass


T = TypeVar('T', bound=Union[KeyHandlerCallable, Binding])


class KeyBindings(KeyBindingsBase):
    """
    A container for a set of key bindings.

    Example usage::

        kb = KeyBindings()

        @kb.add('c-t')
        def _(event):
            print('Control-T pressed')

        @kb.add('c-a', 'c-b')
        def _(event):
            print('Control-A pressed, followed by Control-B')

        @kb.add('c-x', filter=is_searching)
        def _(event):
            print('Control-X pressed')  # Works only if we are searching.

    """

    def __init__(self) ->None:
        self._bindings: list[Binding] = []
        self._get_bindings_for_keys_cache: SimpleCache[KeysTuple, list[Binding]
            ] = SimpleCache(maxsize=10000)
        self._get_bindings_starting_with_keys_cache: SimpleCache[KeysTuple,
            list[Binding]] = SimpleCache(maxsize=1000)
        self.__version = 0

    def add(self, *keys: (Keys | str), filter: FilterOrBool=True, eager:
        FilterOrBool=False, is_global: FilterOrBool=False, save_before:
        Callable[[KeyPressEvent], bool]=lambda e: True, record_in_macro:
        FilterOrBool=True) ->Callable[[T], T]:
        """
        Decorator for adding a key bindings.

        :param filter: :class:`~prompt_toolkit.filters.Filter` to determine
            when this key binding is active.
        :param eager: :class:`~prompt_toolkit.filters.Filter` or `bool`.
            When True, ignore potential longer matches when this key binding is
            hit. E.g. when there is an active eager key binding for Ctrl-X,
            execute the handler immediately and ignore the key binding for
            Ctrl-X Ctrl-E of which it is a prefix.
        :param is_global: When this key bindings is added to a `Container` or
            `Control`, make it a global (always active) binding.
        :param save_before: Callable that takes an `Event` and returns True if
            we should save the current buffer, before handling the event.
            (That's the default.)
        :param record_in_macro: Record these key bindings when a macro is
            being recorded. (True by default.)
        """
        pass

    def remove(self, *args: (Keys | str | KeyHandlerCallable)) ->None:
        """
        Remove a key binding.

        This expects either a function that was given to `add` method as
        parameter or a sequence of key bindings.

        Raises `ValueError` when no bindings was found.

        Usage::

            remove(handler)  # Pass handler.
            remove('c-x', 'c-a')  # Or pass the key bindings.
        """
        pass
    add_binding = add
    remove_binding = remove

    def get_bindings_for_keys(self, keys: KeysTuple) ->list[Binding]:
        """
        Return a list of key bindings that can handle this key.
        (This return also inactive bindings, so the `filter` still has to be
        called, for checking it.)

        :param keys: tuple of keys.
        """
        pass

    def get_bindings_starting_with_keys(self, keys: KeysTuple) ->list[Binding]:
        """
        Return a list of key bindings that handle a key sequence starting with
        `keys`. (It does only return bindings for which the sequences are
        longer than `keys`. And like `get_bindings_for_keys`, it also includes
        inactive bindings.)

        :param keys: tuple of keys.
        """
        pass


def _parse_key(key: (Keys | str)) ->(str | Keys):
    """
    Replace key by alias and verify whether it's a valid one.
    """
    pass


def key_binding(filter: FilterOrBool=True, eager: FilterOrBool=False,
    is_global: FilterOrBool=False, save_before: Callable[[KeyPressEvent],
    bool]=lambda event: True, record_in_macro: FilterOrBool=True) ->Callable[
    [KeyHandlerCallable], Binding]:
    """
    Decorator that turn a function into a `Binding` object. This can be added
    to a `KeyBindings` object when a key binding is assigned.
    """
    pass


class _Proxy(KeyBindingsBase):
    """
    Common part for ConditionalKeyBindings and _MergedKeyBindings.
    """

    def __init__(self) ->None:
        self._bindings2: KeyBindingsBase = KeyBindings()
        self._last_version: Hashable = ()

    def _update_cache(self) ->None:
        """
        If `self._last_version` is outdated, then this should update
        the version and `self._bindings2`.
        """
        pass


class ConditionalKeyBindings(_Proxy):
    """
    Wraps around a `KeyBindings`. Disable/enable all the key bindings according to
    the given (additional) filter.::

        @Condition
        def setting_is_true():
            return True  # or False

        registry = ConditionalKeyBindings(key_bindings, setting_is_true)

    When new key bindings are added to this object. They are also
    enable/disabled according to the given `filter`.

    :param registries: List of :class:`.KeyBindings` objects.
    :param filter: :class:`~prompt_toolkit.filters.Filter` object.
    """

    def __init__(self, key_bindings: KeyBindingsBase, filter: FilterOrBool=True
        ) ->None:
        _Proxy.__init__(self)
        self.key_bindings = key_bindings
        self.filter = to_filter(filter)

    def _update_cache(self) ->None:
        """If the original key bindings was changed. Update our copy version."""
        pass


class _MergedKeyBindings(_Proxy):
    """
    Merge multiple registries of key bindings into one.

    This class acts as a proxy to multiple :class:`.KeyBindings` objects, but
    behaves as if this is just one bigger :class:`.KeyBindings`.

    :param registries: List of :class:`.KeyBindings` objects.
    """

    def __init__(self, registries: Sequence[KeyBindingsBase]) ->None:
        _Proxy.__init__(self)
        self.registries = registries

    def _update_cache(self) ->None:
        """
        If one of the original registries was changed. Update our merged
        version.
        """
        pass


def merge_key_bindings(bindings: Sequence[KeyBindingsBase]
    ) ->_MergedKeyBindings:
    """
    Merge multiple :class:`.Keybinding` objects together.

    Usage::

        bindings = merge_key_bindings([bindings1, bindings2, ...])
    """
    pass


class DynamicKeyBindings(_Proxy):
    """
    KeyBindings class that can dynamically returns any KeyBindings.

    :param get_key_bindings: Callable that returns a :class:`.KeyBindings` instance.
    """

    def __init__(self, get_key_bindings: Callable[[], KeyBindingsBase | None]
        ) ->None:
        self.get_key_bindings = get_key_bindings
        self.__version = 0
        self._last_child_version = None
        self._dummy = KeyBindings()


class GlobalOnlyKeyBindings(_Proxy):
    """
    Wrapper around a :class:`.KeyBindings` object that only exposes the global
    key bindings.
    """

    def __init__(self, key_bindings: KeyBindingsBase) ->None:
        _Proxy.__init__(self)
        self.key_bindings = key_bindings

    def _update_cache(self) ->None:
        """
        If one of the original registries was changed. Update our merged
        version.
        """
        pass
