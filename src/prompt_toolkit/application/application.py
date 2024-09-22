from __future__ import annotations
import asyncio
import contextvars
import os
import re
import signal
import sys
import threading
import time
from asyncio import AbstractEventLoop, Future, Task, ensure_future, get_running_loop, sleep
from contextlib import ExitStack, contextmanager
from subprocess import Popen
from traceback import format_tb
from typing import Any, Callable, Coroutine, Generator, Generic, Hashable, Iterable, Iterator, TypeVar, cast, overload
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.cache import SimpleCache
from prompt_toolkit.clipboard import Clipboard, InMemoryClipboard
from prompt_toolkit.cursor_shapes import AnyCursorShapeConfig, to_cursor_shape_config
from prompt_toolkit.data_structures import Size
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.eventloop import InputHook, get_traceback_from_context, new_eventloop_with_inputhook, run_in_executor_with_context
from prompt_toolkit.eventloop.utils import call_soon_threadsafe
from prompt_toolkit.filters import Condition, Filter, FilterOrBool, to_filter
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.input.base import Input
from prompt_toolkit.input.typeahead import get_typeahead, store_typeahead
from prompt_toolkit.key_binding.bindings.page_navigation import load_page_navigation_bindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.emacs_state import EmacsState
from prompt_toolkit.key_binding.key_bindings import Binding, ConditionalKeyBindings, GlobalOnlyKeyBindings, KeyBindings, KeyBindingsBase, KeysTuple, merge_key_bindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent, KeyProcessor
from prompt_toolkit.key_binding.vi_state import ViState
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import Container, Window
from prompt_toolkit.layout.controls import BufferControl, UIControl
from prompt_toolkit.layout.dummy import create_dummy_layout
from prompt_toolkit.layout.layout import Layout, walk
from prompt_toolkit.output import ColorDepth, Output
from prompt_toolkit.renderer import Renderer, print_formatted_text
from prompt_toolkit.search import SearchState
from prompt_toolkit.styles import BaseStyle, DummyStyle, DummyStyleTransformation, DynamicStyle, StyleTransformation, default_pygments_style, default_ui_style, merge_styles
from prompt_toolkit.utils import Event, in_main_thread
from .current import get_app_session, set_app
from .run_in_terminal import in_terminal, run_in_terminal
__all__ = ['Application']
E = KeyPressEvent
_AppResult = TypeVar('_AppResult')
ApplicationEventHandler = Callable[['Application[_AppResult]'], None]
_SIGWINCH = getattr(signal, 'SIGWINCH', None)
_SIGTSTP = getattr(signal, 'SIGTSTP', None)


class Application(Generic[_AppResult]):
    """
    The main Application class!
    This glues everything together.

    :param layout: A :class:`~prompt_toolkit.layout.Layout` instance.
    :param key_bindings:
        :class:`~prompt_toolkit.key_binding.KeyBindingsBase` instance for
        the key bindings.
    :param clipboard: :class:`~prompt_toolkit.clipboard.Clipboard` to use.
    :param full_screen: When True, run the application on the alternate screen buffer.
    :param color_depth: Any :class:`~.ColorDepth` value, a callable that
        returns a :class:`~.ColorDepth` or `None` for default.
    :param erase_when_done: (bool) Clear the application output when it finishes.
    :param reverse_vi_search_direction: Normally, in Vi mode, a '/' searches
        forward and a '?' searches backward. In Readline mode, this is usually
        reversed.
    :param min_redraw_interval: Number of seconds to wait between redraws. Use
        this for applications where `invalidate` is called a lot. This could cause
        a lot of terminal output, which some terminals are not able to process.

        `None` means that every `invalidate` will be scheduled right away
        (which is usually fine).

        When one `invalidate` is called, but a scheduled redraw of a previous
        `invalidate` call has not been executed yet, nothing will happen in any
        case.

    :param max_render_postpone_time: When there is high CPU (a lot of other
        scheduled calls), postpone the rendering max x seconds.  '0' means:
        don't postpone. '.5' means: try to draw at least twice a second.

    :param refresh_interval: Automatically invalidate the UI every so many
        seconds. When `None` (the default), only invalidate when `invalidate`
        has been called.

    :param terminal_size_polling_interval: Poll the terminal size every so many
        seconds. Useful if the applications runs in a thread other then then
        main thread where SIGWINCH can't be handled, or on Windows.

    Filters:

    :param mouse_support: (:class:`~prompt_toolkit.filters.Filter` or
        boolean). When True, enable mouse support.
    :param paste_mode: :class:`~prompt_toolkit.filters.Filter` or boolean.
    :param editing_mode: :class:`~prompt_toolkit.enums.EditingMode`.

    :param enable_page_navigation_bindings: When `True`, enable the page
        navigation key bindings. These include both Emacs and Vi bindings like
        page-up, page-down and so on to scroll through pages. Mostly useful for
        creating an editor or other full screen applications. Probably, you
        don't want this for the implementation of a REPL. By default, this is
        enabled if `full_screen` is set.

    Callbacks (all of these should accept an
    :class:`~prompt_toolkit.application.Application` object as input.)

    :param on_reset: Called during reset.
    :param on_invalidate: Called when the UI has been invalidated.
    :param before_render: Called right before rendering.
    :param after_render: Called right after rendering.

    I/O:
    (Note that the preferred way to change the input/output is by creating an
    `AppSession` with the required input/output objects. If you need multiple
    applications running at the same time, you have to create a separate
    `AppSession` using a `with create_app_session():` block.

    :param input: :class:`~prompt_toolkit.input.Input` instance.
    :param output: :class:`~prompt_toolkit.output.Output` instance. (Probably
                   Vt100_Output or Win32Output.)

    Usage:

        app = Application(...)
        app.run()

        # Or
        await app.run_async()
    """

    def __init__(self, layout: (Layout | None)=None, style: (BaseStyle |
        None)=None, include_default_pygments_style: FilterOrBool=True,
        style_transformation: (StyleTransformation | None)=None,
        key_bindings: (KeyBindingsBase | None)=None, clipboard: (Clipboard |
        None)=None, full_screen: bool=False, color_depth: (ColorDepth |
        Callable[[], ColorDepth | None] | None)=None, mouse_support:
        FilterOrBool=False, enable_page_navigation_bindings: (None |
        FilterOrBool)=None, paste_mode: FilterOrBool=False, editing_mode:
        EditingMode=EditingMode.EMACS, erase_when_done: bool=False,
        reverse_vi_search_direction: FilterOrBool=False,
        min_redraw_interval: (float | int | None)=None,
        max_render_postpone_time: (float | int | None)=0.01,
        refresh_interval: (float | None)=None,
        terminal_size_polling_interval: (float | None)=0.5, cursor:
        AnyCursorShapeConfig=None, on_reset: (ApplicationEventHandler[
        _AppResult] | None)=None, on_invalidate: (ApplicationEventHandler[
        _AppResult] | None)=None, before_render: (ApplicationEventHandler[
        _AppResult] | None)=None, after_render: (ApplicationEventHandler[
        _AppResult] | None)=None, input: (Input | None)=None, output: (
        Output | None)=None) ->None:
        if enable_page_navigation_bindings is None:
            enable_page_navigation_bindings = Condition(lambda : self.
                full_screen)
        paste_mode = to_filter(paste_mode)
        mouse_support = to_filter(mouse_support)
        reverse_vi_search_direction = to_filter(reverse_vi_search_direction)
        enable_page_navigation_bindings = to_filter(
            enable_page_navigation_bindings)
        include_default_pygments_style = to_filter(
            include_default_pygments_style)
        if layout is None:
            layout = create_dummy_layout()
        if style_transformation is None:
            style_transformation = DummyStyleTransformation()
        self.style = style
        self.style_transformation = style_transformation
        self.key_bindings = key_bindings
        self._default_bindings = load_key_bindings()
        self._page_navigation_bindings = load_page_navigation_bindings()
        self.layout = layout
        self.clipboard = clipboard or InMemoryClipboard()
        self.full_screen: bool = full_screen
        self._color_depth = color_depth
        self.mouse_support = mouse_support
        self.paste_mode = paste_mode
        self.editing_mode = editing_mode
        self.erase_when_done = erase_when_done
        self.reverse_vi_search_direction = reverse_vi_search_direction
        self.enable_page_navigation_bindings = enable_page_navigation_bindings
        self.min_redraw_interval = min_redraw_interval
        self.max_render_postpone_time = max_render_postpone_time
        self.refresh_interval = refresh_interval
        self.terminal_size_polling_interval = terminal_size_polling_interval
        self.cursor = to_cursor_shape_config(cursor)
        self.on_invalidate = Event(self, on_invalidate)
        self.on_reset = Event(self, on_reset)
        self.before_render = Event(self, before_render)
        self.after_render = Event(self, after_render)
        session = get_app_session()
        self.output = output or session.output
        self.input = input or session.input
        self.pre_run_callables: list[Callable[[], None]] = []
        self._is_running = False
        self.future: Future[_AppResult] | None = None
        self.loop: AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self.context: contextvars.Context | None = None
        self.quoted_insert = False
        self.vi_state = ViState()
        self.emacs_state = EmacsState()
        self.ttimeoutlen = 0.5
        self.timeoutlen = 1.0
        self._merged_style = self._create_merged_style(
            include_default_pygments_style)
        self.renderer = Renderer(self._merged_style, self.output,
            full_screen=full_screen, mouse_support=mouse_support,
            cpr_not_supported_callback=self.cpr_not_supported_callback)
        self.render_counter = 0
        self._invalidated = False
        self._invalidate_events: list[Event[object]] = []
        self._last_redraw_time = 0.0
        self.key_processor = KeyProcessor(_CombinedRegistry(self))
        self._running_in_terminal = False
        self._running_in_terminal_f: Future[None] | None = None
        self.reset()

    def _create_merged_style(self, include_default_pygments_style: Filter
        ) ->BaseStyle:
        """
        Create a `Style` object that merges the default UI style, the default
        pygments style, and the custom user style.
        """
        pass

    @property
    def color_depth(self) ->ColorDepth:
        """
        The active :class:`.ColorDepth`.

        The current value is determined as follows:

        - If a color depth was given explicitly to this application, use that
          value.
        - Otherwise, fall back to the color depth that is reported by the
          :class:`.Output` implementation. If the :class:`.Output` class was
          created using `output.defaults.create_output`, then this value is
          coming from the $PROMPT_TOOLKIT_COLOR_DEPTH environment variable.
        """
        pass

    @property
    def current_buffer(self) ->Buffer:
        """
        The currently focused :class:`~.Buffer`.

        (This returns a dummy :class:`.Buffer` when none of the actual buffers
        has the focus. In this case, it's really not practical to check for
        `None` values or catch exceptions every time.)
        """
        pass

    @property
    def current_search_state(self) ->SearchState:
        """
        Return the current :class:`.SearchState`. (The one for the focused
        :class:`.BufferControl`.)
        """
        pass

    def reset(self) ->None:
        """
        Reset everything, for reading the next input.
        """
        pass

    def invalidate(self) ->None:
        """
        Thread safe way of sending a repaint trigger to the input event loop.
        """
        pass

    @property
    def invalidated(self) ->bool:
        """True when a redraw operation has been scheduled."""
        pass

    def _redraw(self, render_as_done: bool=False) ->None:
        """
        Render the command line again. (Not thread safe!) (From other threads,
        or if unsure, use :meth:`.Application.invalidate`.)

        :param render_as_done: make sure to put the cursor after the UI.
        """
        pass

    def _start_auto_refresh_task(self) ->None:
        """
        Start a while/true loop in the background for automatic invalidation of
        the UI.
        """
        pass

    def _update_invalidate_events(self) ->None:
        """
        Make sure to attach 'invalidate' handlers to all invalidate events in
        the UI.
        """
        pass

    def _invalidate_handler(self, sender: object) ->None:
        """
        Handler for invalidate events coming from UIControls.

        (This handles the difference in signature between event handler and
        `self.invalidate`. It also needs to be a method -not a nested
        function-, so that we can remove it again .)
        """
        pass

    def _on_resize(self) ->None:
        """
        When the window size changes, we erase the current output and request
        again the cursor position. When the CPR answer arrives, the output is
        drawn again.
        """
        pass

    def _pre_run(self, pre_run: (Callable[[], None] | None)=None) ->None:
        """
        Called during `run`.

        `self.future` should be set to the new future at the point where this
        is called in order to avoid data races. `pre_run` can be used to set a
        `threading.Event` to synchronize with UI termination code, running in
        another thread that would call `Application.exit`. (See the progress
        bar code for an example.)
        """
        pass

    async def run_async(self, pre_run: (Callable[[], None] | None)=None,
        set_exception_handler: bool=True, handle_sigint: bool=True,
        slow_callback_duration: float=0.5) ->_AppResult:
        """
        Run the prompt_toolkit :class:`~prompt_toolkit.application.Application`
        until :meth:`~prompt_toolkit.application.Application.exit` has been
        called. Return the value that was passed to
        :meth:`~prompt_toolkit.application.Application.exit`.

        This is the main entry point for a prompt_toolkit
        :class:`~prompt_toolkit.application.Application` and usually the only
        place where the event loop is actually running.

        :param pre_run: Optional callable, which is called right after the
            "reset" of the application.
        :param set_exception_handler: When set, in case of an exception, go out
            of the alternate screen and hide the application, display the
            exception, and wait for the user to press ENTER.
        :param handle_sigint: Handle SIGINT signal if possible. This will call
            the `<sigint>` key binding when a SIGINT is received. (This only
            works in the main thread.)
        :param slow_callback_duration: Display warnings if code scheduled in
            the asyncio event loop takes more time than this. The asyncio
            default of `0.1` is sometimes not sufficient on a slow system,
            because exceptionally, the drawing of the app, which happens in the
            event loop, can take a bit longer from time to time.
        """
        pass

    def run(self, pre_run: (Callable[[], None] | None)=None,
        set_exception_handler: bool=True, handle_sigint: bool=True,
        in_thread: bool=False, inputhook: (InputHook | None)=None
        ) ->_AppResult:
        """
        A blocking 'run' call that waits until the UI is finished.

        This will run the application in a fresh asyncio event loop.

        :param pre_run: Optional callable, which is called right after the
            "reset" of the application.
        :param set_exception_handler: When set, in case of an exception, go out
            of the alternate screen and hide the application, display the
            exception, and wait for the user to press ENTER.
        :param in_thread: When true, run the application in a background
            thread, and block the current thread until the application
            terminates. This is useful if we need to be sure the application
            won't use the current event loop (asyncio does not support nested
            event loops). A new event loop will be created in this background
            thread, and that loop will also be closed when the background
            thread terminates. When this is used, it's especially important to
            make sure that all asyncio background tasks are managed through
            `get_appp().create_background_task()`, so that unfinished tasks are
            properly cancelled before the event loop is closed. This is used
            for instance in ptpython.
        :param handle_sigint: Handle SIGINT signal. Call the key binding for
            `Keys.SIGINT`. (This only works in the main thread.)
        """
        pass

    def _handle_exception(self, loop: AbstractEventLoop, context: dict[str,
        Any]) ->None:
        """
        Handler for event loop exceptions.
        This will print the exception, using run_in_terminal.
        """
        pass

    @contextmanager
    def _enable_breakpointhook(self) ->Generator[None, None, None]:
        """
        Install our custom breakpointhook for the duration of this context
        manager. (We will only install the hook if no other custom hook was
        set.)
        """
        pass

    def _breakpointhook(self, *a: object, **kw: object) ->None:
        """
        Breakpointhook which uses PDB, but ensures that the application is
        hidden and input echoing is restored during each debugger dispatch.

        This can be called from any thread. In any case, the application's
        event loop will be blocked while the PDB input is displayed. The event
        will continue after leaving the debugger.
        """
        pass

    def create_background_task(self, coroutine: Coroutine[Any, Any, None]
        ) ->asyncio.Task[None]:
        """
        Start a background task (coroutine) for the running application. When
        the `Application` terminates, unfinished background tasks will be
        cancelled.

        Given that we still support Python versions before 3.11, we can't use
        task groups (and exception groups), because of that, these background
        tasks are not allowed to raise exceptions. If they do, we'll call the
        default exception handler from the event loop.

        If at some point, we have Python 3.11 as the minimum supported Python
        version, then we can use a `TaskGroup` (with the lifetime of
        `Application.run_async()`, and run run the background tasks in there.

        This is not threadsafe.
        """
        pass

    def _on_background_task_done(self, task: asyncio.Task[None]) ->None:
        """
        Called when a background task completes. Remove it from
        `_background_tasks`, and handle exceptions if any.
        """
        pass

    async def cancel_and_wait_for_background_tasks(self) ->None:
        """
        Cancel all background tasks, and wait for the cancellation to complete.
        If any of the background tasks raised an exception, this will also
        propagate the exception.

        (If we had nurseries like Trio, this would be the `__aexit__` of a
        nursery.)
        """
        pass

    async def _poll_output_size(self) ->None:
        """
        Coroutine for polling the terminal dimensions.

        Useful for situations where `attach_winch_signal_handler` is not sufficient:
        - If we are not running in the main thread.
        - On Windows.
        """
        pass

    def cpr_not_supported_callback(self) ->None:
        """
        Called when we don't receive the cursor position response in time.
        """
        pass

    @overload
    def exit(self) ->None:
        """Exit without arguments."""
        pass

    @overload
    def exit(self, *, result: _AppResult, style: str='') ->None:
        """Exit with `_AppResult`."""
        pass

    @overload
    def exit(self, *, exception: (BaseException | type[BaseException]),
        style: str='') ->None:
        """Exit with exception."""
        pass

    def exit(self, result: (_AppResult | None)=None, exception: (
        BaseException | type[BaseException] | None)=None, style: str=''
        ) ->None:
        """
        Exit application.

        .. note::

            If `Application.exit` is called before `Application.run()` is
            called, then the `Application` won't exit (because the
            `Application.future` doesn't correspond to the current run). Use a
            `pre_run` hook and an event to synchronize the closing if there's a
            chance this can happen.

        :param result: Set this result for the application.
        :param exception: Set this exception as the result for an application. For
            a prompt, this is often `EOFError` or `KeyboardInterrupt`.
        :param style: Apply this style on the whole content when quitting,
            often this is 'class:exiting' for a prompt. (Used when
            `erase_when_done` is not set.)
        """
        pass

    def _request_absolute_cursor_position(self) ->None:
        """
        Send CPR request.
        """
        pass

    async def run_system_command(self, command: str, wait_for_enter: bool=
        True, display_before_text: AnyFormattedText='', wait_text: str=
        'Press ENTER to continue...') ->None:
        """
        Run system command (While hiding the prompt. When finished, all the
        output will scroll above the prompt.)

        :param command: Shell command to be executed.
        :param wait_for_enter: FWait for the user to press enter, when the
            command is finished.
        :param display_before_text: If given, text to be displayed before the
            command executes.
        :return: A `Future` object.
        """
        pass

    def suspend_to_background(self, suspend_group: bool=True) ->None:
        """
        (Not thread safe -- to be called from inside the key bindings.)
        Suspend process.

        :param suspend_group: When true, suspend the whole process group.
            (This is the default, and probably what you want.)
        """
        pass

    def print_text(self, text: AnyFormattedText, style: (BaseStyle | None)=None
        ) ->None:
        """
        Print a list of (style_str, text) tuples to the output.
        (When the UI is running, this method has to be called through
        `run_in_terminal`, otherwise it will destroy the UI.)

        :param text: List of ``(style_str, text)`` tuples.
        :param style: Style class to use. Defaults to the active style in the CLI.
        """
        pass

    @property
    def is_running(self) ->bool:
        """`True` when the application is currently active/running."""
        pass

    def get_used_style_strings(self) ->list[str]:
        """
        Return a list of used style strings. This is helpful for debugging, and
        for writing a new `Style`.
        """
        pass


class _CombinedRegistry(KeyBindingsBase):
    """
    The `KeyBindings` of key bindings for a `Application`.
    This merges the global key bindings with the one of the current user
    control.
    """

    def __init__(self, app: Application[_AppResult]) ->None:
        self.app = app
        self._cache: SimpleCache[tuple[Window, frozenset[UIControl]],
            KeyBindingsBase] = SimpleCache()

    @property
    def _version(self) ->Hashable:
        """Not needed - this object is not going to be wrapped in another
        KeyBindings object."""
        pass

    @property
    def bindings(self) ->list[Binding]:
        """Not needed - this object is not going to be wrapped in another
        KeyBindings object."""
        pass

    def _create_key_bindings(self, current_window: Window, other_controls:
        list[UIControl]) ->KeyBindingsBase:
        """
        Create a `KeyBindings` object that merges the `KeyBindings` from the
        `UIControl` with all the parent controls and the global key bindings.
        """
        pass


async def _do_wait_for_enter(wait_text: AnyFormattedText) ->None:
    """
    Create a sub application to wait for the enter key press.
    This has two advantages over using 'input'/'raw_input':
    - This will share the same input/output I/O.
    - This doesn't block the event loop.
    """
    pass


@contextmanager
def attach_winch_signal_handler(handler: Callable[[], None]) ->Generator[
    None, None, None]:
    """
    Attach the given callback as a WINCH signal handler within the context
    manager. Restore the original signal handler when done.

    The `Application.run` method will register SIGWINCH, so that it will
    properly repaint when the terminal window resizes. However, using
    `run_in_terminal`, we can temporarily send an application to the
    background, and run an other app in between, which will then overwrite the
    SIGWINCH. This is why it's important to restore the handler when the app
    terminates.
    """
    pass
