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
        logger.debug(f"Received DO command: {data}")
        # Respond with WILL if we support the option, WONT otherwise
        # This is a simplified implementation
        self.feed(IAC + WILL + data)

    def dont_received(self, data: bytes) ->None:
        """Received telnet DONT command."""
        logger.debug(f"Received DONT command: {data}")
        # Acknowledge the DONT command
        self.feed(IAC + WONT + data)

    def will_received(self, data: bytes) ->None:
        """Received telnet WILL command."""
        logger.debug(f"Received WILL command: {data}")
        # Respond with DO if we want to enable the option, DONT otherwise
        # This is a simplified implementation
        self.feed(IAC + DO + data)

    def wont_received(self, data: bytes) ->None:
        """Received telnet WONT command."""
        logger.debug(f"Received WONT command: {data}")
        # Acknowledge the WONT command
        self.feed(IAC + DONT + data)

    def naws(self, data: bytes) ->None:
        """
        Received NAWS. (Window dimensions.)
        """
        if len(data) == 4:
            columns, rows = struct.unpack('!HH', data)
            logger.debug(f"Received NAWS: {columns}x{rows}")
            self.size_received_callback(rows, columns)
        else:
            logger.warning(f"Invalid NAWS data received: {data}")

    def ttype(self, data: bytes) ->None:
        """
        Received terminal type.
        """
        if data.startswith(IS):
            terminal_type = data[1:].decode('ascii', errors='ignore')
            logger.debug(f"Received terminal type: {terminal_type}")
            self.ttype_received_callback(terminal_type)
        else:
            logger.warning(f"Invalid TTYPE data received: {data}")

    def negotiate(self, data: bytes) ->None:
        """
        Got negotiate data.
        """
        logger.debug(f"Negotiating: {data}")
        # This method can be expanded to handle specific negotiation scenarios
        # For now, we'll just log the data

    def _parse_coroutine(self) ->Generator[None, bytes, None]:
        """
        Parser state machine.
        Every 'yield' expression returns the next byte.
        """
        while True:
            d = yield
            if d == IAC:
                d = yield
                if d == IAC:
                    self.data_received_callback(IAC)
                elif d in (DO, DONT, WILL, WONT):
                    command = d
                    d = yield
                    if command == DO:
                        self.do_received(d)
                    elif command == DONT:
                        self.dont_received(d)
                    elif command == WILL:
                        self.will_received(d)
                    elif command == WONT:
                        self.wont_received(d)
                elif d == SB:
                    buffer = []
                    while True:
                        d = yield
                        if d == IAC:
                            d = yield
                            if d == SE:
                                break
                        buffer.append(d)
                    buffer = b''.join(buffer)
                    if buffer.startswith(NAWS):
                        self.naws(buffer[1:])
                    elif buffer.startswith(TTYPE):
                        self.ttype(buffer[1:])
                    else:
                        self.negotiate(buffer)
                else:
                    self.negotiate(d)
            else:
                self.data_received_callback(d)

    def feed(self, data: bytes) ->None:
        """
        Feed data to the parser.
        """
        for b in data:
            self._parser.send(bytes([b]))
