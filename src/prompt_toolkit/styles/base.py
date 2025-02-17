"""
The base classes for the styling.
"""
from __future__ import annotations
from abc import ABCMeta, abstractmethod, abstractproperty
from typing import Callable, Hashable, NamedTuple
__all__ = ['Attrs', 'DEFAULT_ATTRS', 'ANSI_COLOR_NAMES',
    'ANSI_COLOR_NAMES_ALIASES', 'BaseStyle', 'DummyStyle', 'DynamicStyle']


class Attrs(NamedTuple):
    color: str | None
    bgcolor: str | None
    bold: bool | None
    underline: bool | None
    strike: bool | None
    italic: bool | None
    blink: bool | None
    reverse: bool | None
    hidden: bool | None


"""
:param color: Hexadecimal string. E.g. '000000' or Ansi color name: e.g. 'ansiblue'
:param bgcolor: Hexadecimal string. E.g. 'ffffff' or Ansi color name: e.g. 'ansired'
:param bold: Boolean
:param underline: Boolean
:param strike: Boolean
:param italic: Boolean
:param blink: Boolean
:param reverse: Boolean
:param hidden: Boolean
"""
DEFAULT_ATTRS = Attrs(color='', bgcolor='', bold=False, underline=False,
    strike=False, italic=False, blink=False, reverse=False, hidden=False)
ANSI_COLOR_NAMES = ['ansidefault', 'ansiblack', 'ansired', 'ansigreen',
    'ansiyellow', 'ansiblue', 'ansimagenta', 'ansicyan', 'ansigray',
    'ansibrightblack', 'ansibrightred', 'ansibrightgreen',
    'ansibrightyellow', 'ansibrightblue', 'ansibrightmagenta',
    'ansibrightcyan', 'ansiwhite']
ANSI_COLOR_NAMES_ALIASES: dict[str, str] = {'ansidarkgray':
    'ansibrightblack', 'ansiteal': 'ansicyan', 'ansiturquoise':
    'ansibrightcyan', 'ansibrown': 'ansiyellow', 'ansipurple':
    'ansimagenta', 'ansifuchsia': 'ansibrightmagenta', 'ansilightgray':
    'ansigray', 'ansidarkred': 'ansired', 'ansidarkgreen': 'ansigreen',
    'ansidarkblue': 'ansiblue'}
assert set(ANSI_COLOR_NAMES_ALIASES.values()).issubset(set(ANSI_COLOR_NAMES))
assert not set(ANSI_COLOR_NAMES_ALIASES.keys()) & set(ANSI_COLOR_NAMES)


class BaseStyle(metaclass=ABCMeta):
    """
    Abstract base class for prompt_toolkit styles.
    """

    @abstractmethod
    def get_attrs_for_style_str(self, style_str: str, default: Attrs=
        DEFAULT_ATTRS) ->Attrs:
        """
        Return :class:`.Attrs` for the given style string.

        :param style_str: The style string. This can contain inline styling as
            well as classnames (e.g. "class:title").
        :param default: `Attrs` to be used if no styling was defined.
        """
        raise NotImplementedError

    @abstractproperty
    def style_rules(self) ->list[tuple[str, str]]:
        """
        The list of style rules, used to create this style.
        (Required for `DynamicStyle` and `_MergedStyle` to work.)
        """
        raise NotImplementedError

    @abstractmethod
    def invalidation_hash(self) ->Hashable:
        """
        Invalidation hash for the style. When this changes over time, the
        renderer knows that something in the style changed, and that everything
        has to be redrawn.
        """
        raise NotImplementedError


class DummyStyle(BaseStyle):
    """
    A style that doesn't style anything.
    """
    def get_attrs_for_style_str(self, style_str: str, default: Attrs=DEFAULT_ATTRS) ->Attrs:
        return default

    @property
    def style_rules(self) ->list[tuple[str, str]]:
        return []

    def invalidation_hash(self) ->Hashable:
        return None


class DynamicStyle(BaseStyle):
    """
    Style class that can dynamically returns an other Style.

    :param get_style: Callable that returns a :class:`.Style` instance.
    """

    def __init__(self, get_style: Callable[[], BaseStyle | None]):
        self.get_style = get_style
        self._dummy = DummyStyle()

    def get_attrs_for_style_str(self, style_str: str, default: Attrs=DEFAULT_ATTRS) ->Attrs:
        style = self.get_style() or self._dummy
        return style.get_attrs_for_style_str(style_str, default)

    @property
    def style_rules(self) ->list[tuple[str, str]]:
        style = self.get_style() or self._dummy
        return style.style_rules

    def invalidation_hash(self) ->Hashable:
        style = self.get_style() or self._dummy
        return (self.get_style, style.invalidation_hash())
