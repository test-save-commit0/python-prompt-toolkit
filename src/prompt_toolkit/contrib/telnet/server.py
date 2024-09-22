"""
Telnet server.
"""
from __future__ import annotations
import asyncio
import contextvars
import socket
from asyncio import get_running_loop
from typing import Any, Callable, Coroutine, TextIO, cast
from prompt_toolkit.application.current import create_app_session, get_app
from prompt_toolkit.application.run_in_terminal import run_in_terminal
from prompt_toolkit.data_structures import Size
from prompt_toolkit.formatted_text import AnyFormattedText, to_formatted_text
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.renderer import print_formatted_text as print_formatted_text
from prompt_toolkit.styles import BaseStyle, DummyStyle
from .log import logger
from .protocol import DO, ECHO, IAC, LINEMODE, MODE, NAWS, SB, SE, SEND, SUPPRESS_GO_AHEAD, TTYPE, WILL, TelnetProtocolParser
__all__ = ['TelnetServer']


class _ConnectionStdout:
    """
    Wrapper around socket which provides `write` and `flush` methods for the
    Vt100_Output output.
    """

    def __init__(self, connection: socket.socket, encoding: str) ->None:
        self._encoding = encoding
        self._connection = connection
        self._errors = 'strict'
        self._buffer: list[bytes] = []
        self._closed = False


class TelnetConnection:
    """
    Class that represents one Telnet connection.
    """

    def __init__(self, conn: socket.socket, addr: tuple[str, int], interact:
        Callable[[TelnetConnection], Coroutine[Any, Any, None]], server:
        TelnetServer, encoding: str, style: (BaseStyle | None), vt100_input:
        PipeInput, enable_cpr: bool=True) ->None:
        self.conn = conn
        self.addr = addr
        self.interact = interact
        self.server = server
        self.encoding = encoding
        self.style = style
        self._closed = False
        self._ready = asyncio.Event()
        self.vt100_input = vt100_input
        self.enable_cpr = enable_cpr
        self.vt100_output: Vt100_Output | None = None
        self.size = Size(rows=40, columns=79)
        _initialize_telnet(conn)

        def get_size() ->Size:
            return self.size
        self.stdout = cast(TextIO, _ConnectionStdout(conn, encoding=encoding))

        def data_received(data: bytes) ->None:
            """TelnetProtocolParser 'data_received' callback"""
            self.vt100_input.send_bytes(data)

        def size_received(rows: int, columns: int) ->None:
            """TelnetProtocolParser 'size_received' callback"""
            self.size = Size(rows=rows, columns=columns)
            if self.vt100_output is not None and self.context:
                self.context.run(lambda : get_app()._on_resize())

        def ttype_received(ttype: str) ->None:
            """TelnetProtocolParser 'ttype_received' callback"""
            self.vt100_output = Vt100_Output(self.stdout, get_size, term=
                ttype, enable_cpr=enable_cpr)
            self._ready.set()
        self.parser = TelnetProtocolParser(data_received, size_received,
            ttype_received)
        self.context: contextvars.Context | None = None

    async def run_application(self) ->None:
        """
        Run application.
        """
        pass

    def feed(self, data: bytes) ->None:
        """
        Handler for incoming data. (Called by TelnetServer.)
        """
        pass

    def close(self) ->None:
        """
        Closed by client.
        """
        pass

    def send(self, formatted_text: AnyFormattedText) ->None:
        """
        Send text to the client.
        """
        pass

    def send_above_prompt(self, formatted_text: AnyFormattedText) ->None:
        """
        Send text to the client.
        This is asynchronous, returns a `Future`.
        """
        pass

    def erase_screen(self) ->None:
        """
        Erase the screen and move the cursor to the top.
        """
        pass


class TelnetServer:
    """
    Telnet server implementation.

    Example::

        async def interact(connection):
            connection.send("Welcome")
            session = PromptSession()
            result = await session.prompt_async(message="Say something: ")
            connection.send(f"You said: {result}
")

        async def main():
            server = TelnetServer(interact=interact, port=2323)
            await server.run()
    """

    def __init__(self, host: str='127.0.0.1', port: int=23, interact:
        Callable[[TelnetConnection], Coroutine[Any, Any, None]]=
        _dummy_interact, encoding: str='utf-8', style: (BaseStyle | None)=
        None, enable_cpr: bool=True) ->None:
        self.host = host
        self.port = port
        self.interact = interact
        self.encoding = encoding
        self.style = style
        self.enable_cpr = enable_cpr
        self._run_task: asyncio.Task[None] | None = None
        self._application_tasks: list[asyncio.Task[None]] = []
        self.connections: set[TelnetConnection] = set()

    async def run(self, ready_cb: (Callable[[], None] | None)=None) ->None:
        """
        Run the telnet server, until this gets cancelled.

        :param ready_cb: Callback that will be called at the point that we're
            actually listening.
        """
        pass

    def start(self) ->None:
        """
        Deprecated: Use `.run()` instead.

        Start the telnet server (stop by calling and awaiting `stop()`).
        """
        pass

    async def stop(self) ->None:
        """
        Deprecated: Use `.run()` instead.

        Stop a telnet server that was started using `.start()` and wait for the
        cancellation to complete.
        """
        pass

    def _accept(self, listen_socket: socket.socket) ->None:
        """
        Accept new incoming connection.
        """
        pass
