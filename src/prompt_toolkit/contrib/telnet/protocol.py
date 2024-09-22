"""
Parser for the Telnet protocol. (Not a complete implementation of the telnet
specification, but sufficient for a command line interface.)

Inspired by `Twisted.conch.telnet`.
"""
from __future__ import annotations
import struct
from typing import Callable, Generator
from .log import logger
__all__ = ['TelnetProtocolParser']
NOP = int2byte(0)
SGA = int2byte(3)
IAC = int2byte(255)
DO = int2byte(253)
DONT = int2byte(254)
LINEMODE = int2byte(34)
SB = int2byte(250)
WILL = int2byte(251)
WONT = int2byte(252)
MODE = int2byte(1)
SE = int2byte(240)
ECHO = int2byte(1)
NAWS = int2byte(31)
LINEMODE = int2byte(34)
SUPPRESS_GO_AHEAD = int2byte(3)
TTYPE = int2byte(24)
SEND = int2byte(1)
IS = int2byte(0)
DM = int2byte(242)
BRK = int2byte(243)
IP = int2byte(244)
AO = int2byte(245)
AYT = int2byte(246)
EC = int2byte(247)
EL = int2byte(248)
GA = int2byte(249)


class TelnetProtocolParser:
    """
    Parser for the Telnet protocol.
    Usage::

        def data_received(data):
            print(data)

        def size_received(rows, columns):
            print(rows, columns)

        p = TelnetProtocolParser(data_received, size_received)
        p.feed(binary_data)
    """

    def __init__(self, data_received_callback: Callable[[bytes], None],
        size_received_callback: Callable[[int, int], None],
        ttype_received_callback: Callable[[str], None]) ->None:
        self.data_received_callback = data_received_callback
        self.size_received_callback = size_received_callback
        self.ttype_received_callback = ttype_received_callback
        self._parser = self._parse_coroutine()
        self._parser.send(None)

    def do_received(self, data: bytes) ->None:
        """Received telnet DO command."""
        pass

    def dont_received(self, data: bytes) ->None:
        """Received telnet DONT command."""
        pass

    def will_received(self, data: bytes) ->None:
        """Received telnet WILL command."""
        pass

    def wont_received(self, data: bytes) ->None:
        """Received telnet WONT command."""
        pass

    def naws(self, data: bytes) ->None:
        """
        Received NAWS. (Window dimensions.)
        """
        pass

    def ttype(self, data: bytes) ->None:
        """
        Received terminal type.
        """
        pass

    def negotiate(self, data: bytes) ->None:
        """
        Got negotiate data.
        """
        pass

    def _parse_coroutine(self) ->Generator[None, bytes, None]:
        """
        Parser state machine.
        Every 'yield' expression returns the next byte.
        """
        pass

    def feed(self, data: bytes) ->None:
        """
        Feed data to the parser.
        """
        pass
