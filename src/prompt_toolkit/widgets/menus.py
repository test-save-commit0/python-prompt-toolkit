from __future__ import annotations
from typing import Callable, Iterable, Sequence
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text.base import OneStyleAndTextTuple, StyleAndTextTuples
from prompt_toolkit.key_binding.key_bindings import KeyBindings, KeyBindingsBase
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import AnyContainer, ConditionalContainer, Container, Float, FloatContainer, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.utils import get_cwidth
from prompt_toolkit.widgets import Shadow
from .base import Border
__all__ = ['MenuContainer', 'MenuItem']
E = KeyPressEvent


class MenuContainer:
    """
    :param floats: List of extra Float objects to display.
    :param menu_items: List of `MenuItem` objects.
    """

    def __init__(self, body: AnyContainer, menu_items: list[MenuItem],
        floats: (list[Float] | None)=None, key_bindings: (KeyBindingsBase |
        None)=None) ->None:
        self.body = body
        self.menu_items = menu_items
        self.selected_menu = [0]
        kb = KeyBindings()

        @Condition
        def in_main_menu() ->bool:
            return len(self.selected_menu) == 1

        @Condition
        def in_sub_menu() ->bool:
            return len(self.selected_menu) > 1

        @kb.add('left', filter=in_main_menu)
        def _left(event: E) ->None:
            self.selected_menu[0] = max(0, self.selected_menu[0] - 1)

        @kb.add('right', filter=in_main_menu)
        def _right(event: E) ->None:
            self.selected_menu[0] = min(len(self.menu_items) - 1, self.
                selected_menu[0] + 1)

        @kb.add('down', filter=in_main_menu)
        def _down(event: E) ->None:
            self.selected_menu.append(0)

        @kb.add('c-c', filter=in_main_menu)
        @kb.add('c-g', filter=in_main_menu)
        def _cancel(event: E) ->None:
            """Leave menu."""
            event.app.layout.focus_last()

        @kb.add('left', filter=in_sub_menu)
        @kb.add('c-g', filter=in_sub_menu)
        @kb.add('c-c', filter=in_sub_menu)
        def _back(event: E) ->None:
            """Go back to parent menu."""
            if len(self.selected_menu) > 1:
                self.selected_menu.pop()

        @kb.add('right', filter=in_sub_menu)
        def _submenu(event: E) ->None:
            """go into sub menu."""
            if self._get_menu(len(self.selected_menu) - 1).children:
                self.selected_menu.append(0)
            elif len(self.selected_menu) == 2 and self.selected_menu[0] < len(
                self.menu_items) - 1:
                self.selected_menu = [min(len(self.menu_items) - 1, self.
                    selected_menu[0] + 1)]
                if self.menu_items[self.selected_menu[0]].children:
                    self.selected_menu.append(0)

        @kb.add('up', filter=in_sub_menu)
        def _up_in_submenu(event: E) ->None:
            """Select previous (enabled) menu item or return to main menu."""
            menu = self._get_menu(len(self.selected_menu) - 2)
            index = self.selected_menu[-1]
            previous_indexes = [i for i, item in enumerate(menu.children) if
                i < index and not item.disabled]
            if previous_indexes:
                self.selected_menu[-1] = previous_indexes[-1]
            elif len(self.selected_menu) == 2:
                self.selected_menu.pop()

        @kb.add('down', filter=in_sub_menu)
        def _down_in_submenu(event: E) ->None:
            """Select next (enabled) menu item."""
            menu = self._get_menu(len(self.selected_menu) - 2)
            index = self.selected_menu[-1]
            next_indexes = [i for i, item in enumerate(menu.children) if i >
                index and not item.disabled]
            if next_indexes:
                self.selected_menu[-1] = next_indexes[0]

        @kb.add('enter')
        def _click(event: E) ->None:
            """Click the selected menu item."""
            item = self._get_menu(len(self.selected_menu) - 1)
            if item.handler:
                event.app.layout.focus_last()
                item.handler()
        self.control = FormattedTextControl(self._get_menu_fragments,
            key_bindings=kb, focusable=True, show_cursor=False)
        self.window = Window(height=1, content=self.control, style=
            'class:menu-bar')
        submenu = self._submenu(0)
        submenu2 = self._submenu(1)
        submenu3 = self._submenu(2)

        @Condition
        def has_focus() ->bool:
            return get_app().layout.current_window == self.window
        self.container = FloatContainer(content=HSplit([self.window, body]),
            floats=[Float(xcursor=True, ycursor=True, content=
            ConditionalContainer(content=Shadow(body=submenu), filter=
            has_focus)), Float(attach_to_window=submenu, xcursor=True,
            ycursor=True, allow_cover_cursor=True, content=
            ConditionalContainer(content=Shadow(body=submenu2), filter=
            has_focus & Condition(lambda : len(self.selected_menu) >= 1))),
            Float(attach_to_window=submenu2, xcursor=True, ycursor=True,
            allow_cover_cursor=True, content=ConditionalContainer(content=
            Shadow(body=submenu3), filter=has_focus & Condition(lambda : 
            len(self.selected_menu) >= 2)))] + (floats or []), key_bindings
            =key_bindings)

    def __pt_container__(self) ->Container:
        return self.container


class MenuItem:

    def __init__(self, text: str='', handler: (Callable[[], None] | None)=
        None, children: (list[MenuItem] | None)=None, shortcut: (Sequence[
        Keys | str] | None)=None, disabled: bool=False) ->None:
        self.text = text
        self.handler = handler
        self.children = children or []
        self.shortcut = shortcut
        self.disabled = disabled
        self.selected_item = 0
