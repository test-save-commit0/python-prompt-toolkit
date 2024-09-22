"""
Tools for running functions on the terminal above the current application or prompt.
"""
from __future__ import annotations
from asyncio import Future, ensure_future
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable, TypeVar
from prompt_toolkit.eventloop import run_in_executor_with_context
from .current import get_app_or_none
__all__ = ['run_in_terminal', 'in_terminal']
_T = TypeVar('_T')


def run_in_terminal(func: Callable[[], _T], render_cli_done: bool=False,
    in_executor: bool=False) ->Awaitable[_T]:
    """
    Run function on the terminal above the current application or prompt.

    What this does is first hiding the prompt, then running this callable
    (which can safely output to the terminal), and then again rendering the
    prompt which causes the output of this function to scroll above the
    prompt.

    ``func`` is supposed to be a synchronous function. If you need an
    asynchronous version of this function, use the ``in_terminal`` context
    manager directly.

    :param func: The callable to execute.
    :param render_cli_done: When True, render the interface in the
            'Done' state first, then execute the function. If False,
            erase the interface first.
    :param in_executor: When True, run in executor. (Use this for long
        blocking functions, when you don't want to block the event loop.)

    :returns: A `Future`.
    """
    pass


@asynccontextmanager
async def in_terminal(render_cli_done: bool=False) ->AsyncGenerator[None, None
    ]:
    """
    Asynchronous context manager that suspends the current application and runs
    the body in the terminal.

    .. code::

        async def f():
            async with in_terminal():
                call_some_function()
                await call_some_async_function()
    """
    pass
