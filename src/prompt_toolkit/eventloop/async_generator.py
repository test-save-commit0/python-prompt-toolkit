"""
Implementation for async generators.
"""
from __future__ import annotations
from asyncio import get_running_loop
from contextlib import asynccontextmanager
from queue import Empty, Full, Queue
from typing import Any, AsyncGenerator, Callable, Iterable, TypeVar
from .utils import run_in_executor_with_context
__all__ = ['aclosing', 'generator_to_async_generator']
_T_Generator = TypeVar('_T_Generator', bound=AsyncGenerator[Any, None])


@asynccontextmanager
async def aclosing(thing: _T_Generator) ->AsyncGenerator[_T_Generator, None]:
    """Similar to `contextlib.aclosing`, in Python 3.10."""
    try:
        yield thing
    finally:
        await thing.aclose()


DEFAULT_BUFFER_SIZE: int = 1000
_T = TypeVar('_T')


class _Done:
    pass


async def generator_to_async_generator(get_iterable: Callable[[], Iterable[
    _T]], buffer_size: int=DEFAULT_BUFFER_SIZE) ->AsyncGenerator[_T, None]:
    """
    Turn a generator or iterable into an async generator.

    This works by running the generator in a background thread.

    :param get_iterable: Function that returns a generator or iterable when
        called.
    :param buffer_size: Size of the queue between the async consumer and the
        synchronous generator that produces items.
    """
    queue: Queue[_T | _Done] = Queue(maxsize=buffer_size)
    loop = get_running_loop()

    def producer():
        try:
            for item in get_iterable():
                queue.put(item)
        except Exception as e:
            loop.call_soon_threadsafe(lambda: queue.put(e))
        finally:
            queue.put(_Done())

    await run_in_executor_with_context(producer)

    while True:
        try:
            item = await loop.run_in_executor(None, queue.get, True, 0.1)
            if isinstance(item, _Done):
                break
            if isinstance(item, Exception):
                raise item
            yield item
        except Empty:
            pass
