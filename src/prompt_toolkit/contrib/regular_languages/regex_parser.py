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
    tokens = []
    i = 0
    while i < len(input):
        if input[i].isspace():
            i += 1
            continue
        if input[i] == '#':
            while i < len(input) and input[i] != '\n':
                i += 1
            continue
        if input[i] in '()|*+?{}[]':
            tokens.append(input[i])
            i += 1
        elif input[i] == '\\':
            if i + 1 < len(input):
                tokens.append(input[i:i+2])
                i += 2
            else:
                tokens.append(input[i])
                i += 1
        else:
            start = i
            while i < len(input) and input[i] not in '()|*+?{}[]\\' and not input[i].isspace():
                i += 1
            tokens.append(input[start:i])
    return tokens


def parse_regex(regex_tokens: list[str]) ->Node:
    """
    Takes a list of tokens from the tokenizer, and returns a parse tree.
    """
    def parse_sequence():
        sequence = []
        while tokens and tokens[0] not in ')|':
            sequence.append(parse_atom())
        return NodeSequence(sequence) if len(sequence) > 1 else sequence[0] if sequence else None

    def parse_atom():
        if not tokens:
            return None
        token = tokens.pop(0)
        if token == '(':
            node = parse_sequence()
            if tokens and tokens[0] == ')':
                tokens.pop(0)
            return node
        elif token == '[':
            content = ''
            while tokens and tokens[0] != ']':
                content += tokens.pop(0)
            if tokens and tokens[0] == ']':
                tokens.pop(0)
            return Regex(f'[{content}]')
        elif token in '*+?':
            return Repeat(parse_atom(), 0 if token in '*?' else 1, None if token in '*+' else 1)
        elif token == '{':
            min_repeat = max_repeat = ''
            while tokens and tokens[0] not in ',}':
                min_repeat += tokens.pop(0)
            if tokens and tokens[0] == ',':
                tokens.pop(0)
                while tokens and tokens[0] != '}':
                    max_repeat += tokens.pop(0)
            if tokens and tokens[0] == '}':
                tokens.pop(0)
            return Repeat(parse_atom(), int(min_repeat) if min_repeat else 0, int(max_repeat) if max_repeat else None)
        else:
            return Regex(token)

    tokens = regex_tokens.copy()
    result = parse_sequence()
    while tokens:
        if tokens[0] == '|':
            tokens.pop(0)
            result = AnyNode([result, parse_sequence()])
        else:
            break
    return result
