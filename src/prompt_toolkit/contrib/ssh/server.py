"""
Utility for running a prompt_toolkit application in an asyncssh server.
"""
from __future__ import annotations
import asyncio
import traceback
from asyncio import get_running_loop
from typing import Any, Callable, Coroutine, TextIO, cast
import asyncssh
from prompt_toolkit.application.current import AppSession, create_app_session
from prompt_toolkit.data_structures import Size
from prompt_toolkit.input import PipeInput, create_pipe_input
from prompt_toolkit.output.vt100 import Vt100_Output
__all__ = ['PromptToolkitSSHSession', 'PromptToolkitSSHServer']


class PromptToolkitSSHSession(asyncssh.SSHServerSession):

    def __init__(self, interact: Callable[[PromptToolkitSSHSession],
        Coroutine[Any, Any, None]], *, enable_cpr: bool) ->None:
        self.interact = interact
        self.enable_cpr = enable_cpr
        self.interact_task: asyncio.Task[None] | None = None
        self._chan: Any | None = None
        self.app_session: AppSession | None = None
        self._input: PipeInput | None = None
        self._output: Vt100_Output | None = None


        class Stdout:

            def write(s, data: str) ->None:
                try:
                    if self._chan is not None:
                        self._chan.write(data.replace('\n', '\r\n'))
                except BrokenPipeError:
                    pass

            def isatty(s) ->bool:
                return True

            def flush(s) ->None:
                pass

            @property
            def encoding(s) ->str:
                assert self._chan is not None
                return str(self._chan._orig_chan.get_encoding()[0])
        self.stdout = cast(TextIO, Stdout())

    def _get_size(self) ->Size:
        """
        Callable that returns the current `Size`, required by Vt100_Output.
        """
        if self._chan is None:
            return Size(rows=24, columns=80)  # Default size if channel is not available
        width, height, _, _ = self._chan.get_terminal_size()
        return Size(rows=height, columns=width)


class PromptToolkitSSHServer(asyncssh.SSHServer):
    """
    Run a prompt_toolkit application over an asyncssh server.

    This takes one argument, an `interact` function, which is called for each
    connection. This should be an asynchronous function that runs the
    prompt_toolkit applications. This function runs in an `AppSession`, which
    means that we can have multiple UI interactions concurrently.

    Example usage:

    .. code:: python

        async def interact(ssh_session: PromptToolkitSSHSession) -> None:
            await yes_no_dialog("my title", "my text").run_async()

            prompt_session = PromptSession()
            text = await prompt_session.prompt_async("Type something: ")
            print_formatted_text('You said: ', text)

        server = PromptToolkitSSHServer(interact=interact)
        loop = get_running_loop()
        loop.run_until_complete(
            asyncssh.create_server(
                lambda: MySSHServer(interact),
                "",
                port,
                server_host_keys=["/etc/ssh/..."],
            )
        )
        loop.run_forever()

    :param enable_cpr: When `True`, the default, try to detect whether the SSH
        client runs in a terminal that responds to "cursor position requests".
        That way, we can properly determine how much space there is available
        for the UI (especially for drop down menus) to render.
    """

    def __init__(self, interact: Callable[[PromptToolkitSSHSession],
        Coroutine[Any, Any, None]], *, enable_cpr: bool=True) ->None:
        self.interact = interact
        self.enable_cpr = enable_cpr
