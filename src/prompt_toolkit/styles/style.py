"""
Tool for creating styles from a dictionary.
"""
from __future__ import annotations
import itertools
import re
from enum import Enum
from typing import Hashable, TypeVar
from prompt_toolkit.cache import SimpleCache
from .base import ANSI_COLOR_NAMES, ANSI_COLOR_NAMES_ALIASES, DEFAULT_ATTRS, Attrs, BaseStyle
from .named_colors import NAMED_COLORS
__all__ = ['Style', 'parse_color', 'Priority', 'merge_styles']
_named_colors_lowercase = {k.lower(): v.lstrip('#') for k, v in
    NAMED_COLORS.items()}


def parse_color(text: str) ->str:
    """
    Parse/validate color format.

    Like in Pygments, but also support the ANSI color names.
    (These will map to the colors of the 16 color palette.)
    """
    if text in ANSI_COLOR_NAMES:
        return text
    if text.lower() in ANSI_COLOR_NAMES_ALIASES:
        return ANSI_COLOR_NAMES_ALIASES[text.lower()]
    if text.lower() in _named_colors_lowercase:
        return _named_colors_lowercase[text.lower()]
    if text.startswith('#') and len(text) in (4, 7, 9):
        return text
    if re.match(r'^#[0-9a-fA-F]{3}([0-9a-fA-F]{3})?([0-9a-fA-F]{2})?$', text):
        return text
    raise ValueError(f"Wrong color format: {text}")


_EMPTY_ATTRS = Attrs(color=None, bgcolor=None, bold=None, underline=None,
    strike=None, italic=None, blink=None, reverse=None, hidden=None)


def _expand_classname(classname: str) ->list[str]:
    """
    Split a single class name at the `.` operator, and build a list of classes.

    E.g. 'a.b.c' becomes ['a', 'a.b', 'a.b.c']
    """
    parts = classname.split('.')
    return ['.'.join(parts[:i+1]) for i in range(len(parts))]


def _parse_style_str(style_str: str) ->Attrs:
    """
    Take a style string, e.g.  'bg:red #88ff00 class:title'
    and return a `Attrs` instance.
    """
    attrs = _EMPTY_ATTRS._asdict()
    for part in style_str.split():
        if part.startswith('bg:'):
            attrs['bgcolor'] = parse_color(part[3:])
        elif part.startswith('fg:') or part.startswith('color:'):
            attrs['color'] = parse_color(part.split(':', 1)[1])
        elif part in ('bold', 'italic', 'underline', 'strike', 'reverse', 'hidden'):
            attrs[part] = True
        elif part == 'blink':
            attrs['blink'] = True
        elif ':' not in part:
            attrs['color'] = parse_color(part)
    return Attrs(**attrs)


CLASS_NAMES_RE = re.compile('^[a-z0-9.\\s_-]*$')


class Priority(Enum):
    """
    The priority of the rules, when a style is created from a dictionary.

    In a `Style`, rules that are defined later will always override previous
    defined rules, however in a dictionary, the key order was arbitrary before
    Python 3.6. This means that the style could change at random between rules.

    We have two options:

    - `DICT_KEY_ORDER`: This means, iterate through the dictionary, and take
       the key/value pairs in order as they come. This is a good option if you
       have Python >3.6. Rules at the end will override rules at the beginning.
    - `MOST_PRECISE`: keys that are defined with most precision will get higher
      priority. (More precise means: more elements.)
    """
    DICT_KEY_ORDER = 'KEY_ORDER'
    MOST_PRECISE = 'MOST_PRECISE'


default_priority = Priority.DICT_KEY_ORDER


class Style(BaseStyle):
    """
    Create a ``Style`` instance from a list of style rules.

    The `style_rules` is supposed to be a list of ('classnames', 'style') tuples.
    The classnames are a whitespace separated string of class names and the
    style string is just like a Pygments style definition, but with a few
    additions: it supports 'reverse' and 'blink'.

    Later rules always override previous rules.

    Usage::

        Style([
            ('title', '#ff0000 bold underline'),
            ('something-else', 'reverse'),
            ('class1 class2', 'reverse'),
        ])

    The ``from_dict`` classmethod is similar, but takes a dictionary as input.
    """

    def __init__(self, style_rules: list[tuple[str, str]]) ->None:
        class_names_and_attrs = []
        for class_names, style_str in style_rules:
            assert CLASS_NAMES_RE.match(class_names), repr(class_names)
            class_names_set = frozenset(class_names.lower().split())
            attrs = _parse_style_str(style_str)
            class_names_and_attrs.append((class_names_set, attrs))
        self._style_rules = style_rules
        self.class_names_and_attrs = class_names_and_attrs

    @classmethod
    def from_dict(cls, style_dict: dict[str, str], priority: Priority=
        default_priority) ->Style:
        """
        :param style_dict: Style dictionary.
        :param priority: `Priority` value.
        """
        if priority == Priority.DICT_KEY_ORDER:
            return cls(list(style_dict.items()))
        else:  # Priority.MOST_PRECISE
            return cls(sorted(
                style_dict.items(),
                key=lambda item: (-len(item[0].split()), item[0]),
                reverse=True
            ))

    def get_attrs_for_style_str(self, style_str: str, default: Attrs=
        DEFAULT_ATTRS) ->Attrs:
        """
        Get `Attrs` for the given style string.
        """
        list_of_attrs = [default]
        class_names = set()

        for part in style_str.split():
            if part.startswith('class:'):
                class_names.update(_expand_classname(part[6:]))
            else:
                list_of_attrs.append(_parse_style_str(part))

        for names, attr in self.class_names_and_attrs:
            if names & class_names:
                list_of_attrs.append(attr)

        return _merge_attrs(list_of_attrs)


_T = TypeVar('_T')


def _merge_attrs(list_of_attrs: list[Attrs]) ->Attrs:
    """
    Take a list of :class:`.Attrs` instances and merge them into one.
    Every `Attr` in the list can override the styling of the previous one. So,
    the last one has highest priority.
    """
    result = {}
    for attr in list_of_attrs:
        for k, v in attr._asdict().items():
            if v is not None:
                result[k] = v
    return Attrs(**result)


def merge_styles(styles: list[BaseStyle]) ->_MergedStyle:
    """
    Merge multiple `Style` objects.
    """
    return _MergedStyle(styles)


class _MergedStyle(BaseStyle):
    """
    Merge multiple `Style` objects into one.
    This is supposed to ensure consistency: if any of the given styles changes,
    then this style will be updated.
    """

    def __init__(self, styles: list[BaseStyle]) ->None:
        self.styles = styles
        self._style: SimpleCache[Hashable, Style] = SimpleCache(maxsize=1)

    @property
    def _merged_style(self) ->Style:
        """The `Style` object that has the other styles merged together."""
        def get_style():
            style_rules = []
            for style in self.styles:
                if isinstance(style, Style):
                    style_rules.extend(style._style_rules)
                elif isinstance(style, _MergedStyle):
                    style_rules.extend(style._merged_style._style_rules)
            return Style(style_rules)

        return self._style.get(tuple(self.styles), get_style)
