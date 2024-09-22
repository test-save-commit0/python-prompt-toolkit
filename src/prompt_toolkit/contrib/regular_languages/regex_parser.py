"""
Parser for parsing a regular expression.
Take a string representing a regular expression and return the root node of its
parse tree.

usage::

    root_node = parse_regex('(hello|world)')

Remarks:
- The regex parser processes multiline, it ignores all whitespace and supports
  multiple named groups with the same name and #-style comments.

Limitations:
- Lookahead is not supported.
"""
from __future__ import annotations
import re
__all__ = ['Repeat', 'Variable', 'Regex', 'Lookahead', 'tokenize_regex',
    'parse_regex']


class Node:
    """
    Base class for all the grammar nodes.
    (You don't initialize this one.)
    """

    def __add__(self, other_node: Node) ->NodeSequence:
        return NodeSequence([self, other_node])

    def __or__(self, other_node: Node) ->AnyNode:
        return AnyNode([self, other_node])


class AnyNode(Node):
    """
    Union operation (OR operation) between several grammars. You don't
    initialize this yourself, but it's a result of a "Grammar1 | Grammar2"
    operation.
    """

    def __init__(self, children: list[Node]) ->None:
        self.children = children

    def __or__(self, other_node: Node) ->AnyNode:
        return AnyNode(self.children + [other_node])

    def __repr__(self) ->str:
        return f'{self.__class__.__name__}({self.children!r})'


class NodeSequence(Node):
    """
    Concatenation operation of several grammars. You don't initialize this
    yourself, but it's a result of a "Grammar1 + Grammar2" operation.
    """

    def __init__(self, children: list[Node]) ->None:
        self.children = children

    def __add__(self, other_node: Node) ->NodeSequence:
        return NodeSequence(self.children + [other_node])

    def __repr__(self) ->str:
        return f'{self.__class__.__name__}({self.children!r})'


class Regex(Node):
    """
    Regular expression.
    """

    def __init__(self, regex: str) ->None:
        re.compile(regex)
        self.regex = regex

    def __repr__(self) ->str:
        return f'{self.__class__.__name__}(/{self.regex}/)'


class Lookahead(Node):
    """
    Lookahead expression.
    """

    def __init__(self, childnode: Node, negative: bool=False) ->None:
        self.childnode = childnode
        self.negative = negative

    def __repr__(self) ->str:
        return f'{self.__class__.__name__}({self.childnode!r})'


class Variable(Node):
    """
    Mark a variable in the regular grammar. This will be translated into a
    named group. Each variable can have his own completer, validator, etc..

    :param childnode: The grammar which is wrapped inside this variable.
    :param varname: String.
    """

    def __init__(self, childnode: Node, varname: str='') ->None:
        self.childnode = childnode
        self.varname = varname

    def __repr__(self) ->str:
        return '{}(childnode={!r}, varname={!r})'.format(self.__class__.
            __name__, self.childnode, self.varname)


class Repeat(Node):

    def __init__(self, childnode: Node, min_repeat: int=0, max_repeat: (int |
        None)=None, greedy: bool=True) ->None:
        self.childnode = childnode
        self.min_repeat = min_repeat
        self.max_repeat = max_repeat
        self.greedy = greedy

    def __repr__(self) ->str:
        return f'{self.__class__.__name__}(childnode={self.childnode!r})'


def tokenize_regex(input: str) ->list[str]:
    """
    Takes a string, representing a regular expression as input, and tokenizes
    it.

    :param input: string, representing a regular expression.
    :returns: List of tokens.
    """
    pass


def parse_regex(regex_tokens: list[str]) ->Node:
    """
    Takes a list of tokens from the tokenizer, and returns a parse tree.
    """
    pass
