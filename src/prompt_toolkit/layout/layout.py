"""
Wrapper for the layout.
"""
from __future__ import annotations
from typing import Generator, Iterable, Union
from prompt_toolkit.buffer import Buffer
from .containers import AnyContainer, ConditionalContainer, Container, Window, to_container
from .controls import BufferControl, SearchBufferControl, UIControl
__all__ = ['Layout', 'InvalidLayoutError', 'walk']
FocusableElement = Union[str, Buffer, UIControl, AnyContainer]


class Layout:
    """
    The layout for a prompt_toolkit
    :class:`~prompt_toolkit.application.Application`.
    This also keeps track of which user control is focused.

    :param container: The "root" container for the layout.
    :param focused_element: element to be focused initially. (Can be anything
        the `focus` function accepts.)
    """

    def __init__(self, container: AnyContainer, focused_element: (
        FocusableElement | None)=None) ->None:
        self.container = to_container(container)
        self._stack: list[Window] = []
        self.search_links: dict[SearchBufferControl, BufferControl] = {}
        self._child_to_parent: dict[Container, Container] = {}
        if focused_element is None:
            try:
                self._stack.append(next(self.find_all_windows()))
            except StopIteration as e:
                raise InvalidLayoutError(
                    'Invalid layout. The layout does not contain any Window object.'
                    ) from e
        else:
            self.focus(focused_element)
        self.visible_windows: list[Window] = []

    def __repr__(self) ->str:
        return (
            f'Layout({self.container!r}, current_window={self.current_window!r})'
            )

    def find_all_windows(self) ->Generator[Window, None, None]:
        """
        Find all the :class:`.UIControl` objects in this layout.
        """
        pass

    def focus(self, value: FocusableElement) ->None:
        """
        Focus the given UI element.

        `value` can be either:

        - a :class:`.UIControl`
        - a :class:`.Buffer` instance or the name of a :class:`.Buffer`
        - a :class:`.Window`
        - Any container object. In this case we will focus the :class:`.Window`
          from this container that was focused most recent, or the very first
          focusable :class:`.Window` of the container.
        """
        pass

    def has_focus(self, value: FocusableElement) ->bool:
        """
        Check whether the given control has the focus.
        :param value: :class:`.UIControl` or :class:`.Window` instance.
        """
        pass

    @property
    def current_control(self) ->UIControl:
        """
        Get the :class:`.UIControl` to currently has the focus.
        """
        pass

    @current_control.setter
    def current_control(self, control: UIControl) ->None:
        """
        Set the :class:`.UIControl` to receive the focus.
        """
        pass

    @property
    def current_window(self) ->Window:
        """Return the :class:`.Window` object that is currently focused."""
        pass

    @current_window.setter
    def current_window(self, value: Window) ->None:
        """Set the :class:`.Window` object to be currently focused."""
        pass

    @property
    def is_searching(self) ->bool:
        """True if we are searching right now."""
        pass

    @property
    def search_target_buffer_control(self) ->(BufferControl | None):
        """
        Return the :class:`.BufferControl` in which we are searching or `None`.
        """
        pass

    def get_focusable_windows(self) ->Iterable[Window]:
        """
        Return all the :class:`.Window` objects which are focusable (in the
        'modal' area).
        """
        pass

    def get_visible_focusable_windows(self) ->list[Window]:
        """
        Return a list of :class:`.Window` objects that are focusable.
        """
        pass

    @property
    def current_buffer(self) ->(Buffer | None):
        """
        The currently focused :class:`~.Buffer` or `None`.
        """
        pass

    def get_buffer_by_name(self, buffer_name: str) ->(Buffer | None):
        """
        Look in the layout for a buffer with the given name.
        Return `None` when nothing was found.
        """
        pass

    @property
    def buffer_has_focus(self) ->bool:
        """
        Return `True` if the currently focused control is a
        :class:`.BufferControl`. (For instance, used to determine whether the
        default key bindings should be active or not.)
        """
        pass

    @property
    def previous_control(self) ->UIControl:
        """
        Get the :class:`.UIControl` to previously had the focus.
        """
        pass

    def focus_last(self) ->None:
        """
        Give the focus to the last focused control.
        """
        pass

    def focus_next(self) ->None:
        """
        Focus the next visible/focusable Window.
        """
        pass

    def focus_previous(self) ->None:
        """
        Focus the previous visible/focusable Window.
        """
        pass

    def walk(self) ->Iterable[Container]:
        """
        Walk through all the layout nodes (and their children) and yield them.
        """
        pass

    def walk_through_modal_area(self) ->Iterable[Container]:
        """
        Walk through all the containers which are in the current 'modal' part
        of the layout.
        """
        pass

    def update_parents_relations(self) ->None:
        """
        Update child->parent relationships mapping.
        """
        pass

    def get_parent(self, container: Container) ->(Container | None):
        """
        Return the parent container for the given container, or ``None``, if it
        wasn't found.
        """
        pass


class InvalidLayoutError(Exception):
    pass


def walk(container: Container, skip_hidden: bool=False) ->Iterable[Container]:
    """
    Walk through layout, starting at this container.
    """
    pass
