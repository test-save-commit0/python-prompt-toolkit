from __future__ import annotations
import sys
from typing import TYPE_CHECKING
from prompt_toolkit.data_structures import Point
from prompt_toolkit.key_binding.key_processor import KeyPress, KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseButton, MouseEvent, MouseEventType, MouseModifier
from ..key_bindings import KeyBindings
if TYPE_CHECKING:
    from prompt_toolkit.key_binding.key_bindings import NotImplementedOrNone
__all__ = ['load_mouse_bindings']
E = KeyPressEvent
SCROLL_UP = MouseEventType.SCROLL_UP
SCROLL_DOWN = MouseEventType.SCROLL_DOWN
MOUSE_DOWN = MouseEventType.MOUSE_DOWN
MOUSE_MOVE = MouseEventType.MOUSE_MOVE
MOUSE_UP = MouseEventType.MOUSE_UP
NO_MODIFIER: frozenset[MouseModifier] = frozenset()
SHIFT: frozenset[MouseModifier] = frozenset({MouseModifier.SHIFT})
ALT: frozenset[MouseModifier] = frozenset({MouseModifier.ALT})
SHIFT_ALT: frozenset[MouseModifier] = frozenset({MouseModifier.SHIFT,
    MouseModifier.ALT})
CONTROL: frozenset[MouseModifier] = frozenset({MouseModifier.CONTROL})
SHIFT_CONTROL: frozenset[MouseModifier] = frozenset({MouseModifier.SHIFT,
    MouseModifier.CONTROL})
ALT_CONTROL: frozenset[MouseModifier] = frozenset({MouseModifier.ALT,
    MouseModifier.CONTROL})
SHIFT_ALT_CONTROL: frozenset[MouseModifier] = frozenset({MouseModifier.
    SHIFT, MouseModifier.ALT, MouseModifier.CONTROL})
UNKNOWN_MODIFIER: frozenset[MouseModifier] = frozenset()
LEFT = MouseButton.LEFT
MIDDLE = MouseButton.MIDDLE
RIGHT = MouseButton.RIGHT
NO_BUTTON = MouseButton.NONE
UNKNOWN_BUTTON = MouseButton.UNKNOWN
xterm_sgr_mouse_events = {(0, 'm'): (LEFT, MOUSE_UP, NO_MODIFIER), (4, 'm'):
    (LEFT, MOUSE_UP, SHIFT), (8, 'm'): (LEFT, MOUSE_UP, ALT), (12, 'm'): (
    LEFT, MOUSE_UP, SHIFT_ALT), (16, 'm'): (LEFT, MOUSE_UP, CONTROL), (20,
    'm'): (LEFT, MOUSE_UP, SHIFT_CONTROL), (24, 'm'): (LEFT, MOUSE_UP,
    ALT_CONTROL), (28, 'm'): (LEFT, MOUSE_UP, SHIFT_ALT_CONTROL), (1, 'm'):
    (MIDDLE, MOUSE_UP, NO_MODIFIER), (5, 'm'): (MIDDLE, MOUSE_UP, SHIFT), (
    9, 'm'): (MIDDLE, MOUSE_UP, ALT), (13, 'm'): (MIDDLE, MOUSE_UP,
    SHIFT_ALT), (17, 'm'): (MIDDLE, MOUSE_UP, CONTROL), (21, 'm'): (MIDDLE,
    MOUSE_UP, SHIFT_CONTROL), (25, 'm'): (MIDDLE, MOUSE_UP, ALT_CONTROL), (
    29, 'm'): (MIDDLE, MOUSE_UP, SHIFT_ALT_CONTROL), (2, 'm'): (RIGHT,
    MOUSE_UP, NO_MODIFIER), (6, 'm'): (RIGHT, MOUSE_UP, SHIFT), (10, 'm'):
    (RIGHT, MOUSE_UP, ALT), (14, 'm'): (RIGHT, MOUSE_UP, SHIFT_ALT), (18,
    'm'): (RIGHT, MOUSE_UP, CONTROL), (22, 'm'): (RIGHT, MOUSE_UP,
    SHIFT_CONTROL), (26, 'm'): (RIGHT, MOUSE_UP, ALT_CONTROL), (30, 'm'): (
    RIGHT, MOUSE_UP, SHIFT_ALT_CONTROL), (0, 'M'): (LEFT, MOUSE_DOWN,
    NO_MODIFIER), (4, 'M'): (LEFT, MOUSE_DOWN, SHIFT), (8, 'M'): (LEFT,
    MOUSE_DOWN, ALT), (12, 'M'): (LEFT, MOUSE_DOWN, SHIFT_ALT), (16, 'M'):
    (LEFT, MOUSE_DOWN, CONTROL), (20, 'M'): (LEFT, MOUSE_DOWN,
    SHIFT_CONTROL), (24, 'M'): (LEFT, MOUSE_DOWN, ALT_CONTROL), (28, 'M'):
    (LEFT, MOUSE_DOWN, SHIFT_ALT_CONTROL), (1, 'M'): (MIDDLE, MOUSE_DOWN,
    NO_MODIFIER), (5, 'M'): (MIDDLE, MOUSE_DOWN, SHIFT), (9, 'M'): (MIDDLE,
    MOUSE_DOWN, ALT), (13, 'M'): (MIDDLE, MOUSE_DOWN, SHIFT_ALT), (17, 'M'):
    (MIDDLE, MOUSE_DOWN, CONTROL), (21, 'M'): (MIDDLE, MOUSE_DOWN,
    SHIFT_CONTROL), (25, 'M'): (MIDDLE, MOUSE_DOWN, ALT_CONTROL), (29, 'M'):
    (MIDDLE, MOUSE_DOWN, SHIFT_ALT_CONTROL), (2, 'M'): (RIGHT, MOUSE_DOWN,
    NO_MODIFIER), (6, 'M'): (RIGHT, MOUSE_DOWN, SHIFT), (10, 'M'): (RIGHT,
    MOUSE_DOWN, ALT), (14, 'M'): (RIGHT, MOUSE_DOWN, SHIFT_ALT), (18, 'M'):
    (RIGHT, MOUSE_DOWN, CONTROL), (22, 'M'): (RIGHT, MOUSE_DOWN,
    SHIFT_CONTROL), (26, 'M'): (RIGHT, MOUSE_DOWN, ALT_CONTROL), (30, 'M'):
    (RIGHT, MOUSE_DOWN, SHIFT_ALT_CONTROL), (32, 'M'): (LEFT, MOUSE_MOVE,
    NO_MODIFIER), (36, 'M'): (LEFT, MOUSE_MOVE, SHIFT), (40, 'M'): (LEFT,
    MOUSE_MOVE, ALT), (44, 'M'): (LEFT, MOUSE_MOVE, SHIFT_ALT), (48, 'M'):
    (LEFT, MOUSE_MOVE, CONTROL), (52, 'M'): (LEFT, MOUSE_MOVE,
    SHIFT_CONTROL), (56, 'M'): (LEFT, MOUSE_MOVE, ALT_CONTROL), (60, 'M'):
    (LEFT, MOUSE_MOVE, SHIFT_ALT_CONTROL), (33, 'M'): (MIDDLE, MOUSE_MOVE,
    NO_MODIFIER), (37, 'M'): (MIDDLE, MOUSE_MOVE, SHIFT), (41, 'M'): (
    MIDDLE, MOUSE_MOVE, ALT), (45, 'M'): (MIDDLE, MOUSE_MOVE, SHIFT_ALT), (
    49, 'M'): (MIDDLE, MOUSE_MOVE, CONTROL), (53, 'M'): (MIDDLE, MOUSE_MOVE,
    SHIFT_CONTROL), (57, 'M'): (MIDDLE, MOUSE_MOVE, ALT_CONTROL), (61, 'M'):
    (MIDDLE, MOUSE_MOVE, SHIFT_ALT_CONTROL), (34, 'M'): (RIGHT, MOUSE_MOVE,
    NO_MODIFIER), (38, 'M'): (RIGHT, MOUSE_MOVE, SHIFT), (42, 'M'): (RIGHT,
    MOUSE_MOVE, ALT), (46, 'M'): (RIGHT, MOUSE_MOVE, SHIFT_ALT), (50, 'M'):
    (RIGHT, MOUSE_MOVE, CONTROL), (54, 'M'): (RIGHT, MOUSE_MOVE,
    SHIFT_CONTROL), (58, 'M'): (RIGHT, MOUSE_MOVE, ALT_CONTROL), (62, 'M'):
    (RIGHT, MOUSE_MOVE, SHIFT_ALT_CONTROL), (35, 'M'): (NO_BUTTON,
    MOUSE_MOVE, NO_MODIFIER), (39, 'M'): (NO_BUTTON, MOUSE_MOVE, SHIFT), (
    43, 'M'): (NO_BUTTON, MOUSE_MOVE, ALT), (47, 'M'): (NO_BUTTON,
    MOUSE_MOVE, SHIFT_ALT), (51, 'M'): (NO_BUTTON, MOUSE_MOVE, CONTROL), (
    55, 'M'): (NO_BUTTON, MOUSE_MOVE, SHIFT_CONTROL), (59, 'M'): (NO_BUTTON,
    MOUSE_MOVE, ALT_CONTROL), (63, 'M'): (NO_BUTTON, MOUSE_MOVE,
    SHIFT_ALT_CONTROL), (64, 'M'): (NO_BUTTON, SCROLL_UP, NO_MODIFIER), (68,
    'M'): (NO_BUTTON, SCROLL_UP, SHIFT), (72, 'M'): (NO_BUTTON, SCROLL_UP,
    ALT), (76, 'M'): (NO_BUTTON, SCROLL_UP, SHIFT_ALT), (80, 'M'): (
    NO_BUTTON, SCROLL_UP, CONTROL), (84, 'M'): (NO_BUTTON, SCROLL_UP,
    SHIFT_CONTROL), (88, 'M'): (NO_BUTTON, SCROLL_UP, ALT_CONTROL), (92,
    'M'): (NO_BUTTON, SCROLL_UP, SHIFT_ALT_CONTROL), (65, 'M'): (NO_BUTTON,
    SCROLL_DOWN, NO_MODIFIER), (69, 'M'): (NO_BUTTON, SCROLL_DOWN, SHIFT),
    (73, 'M'): (NO_BUTTON, SCROLL_DOWN, ALT), (77, 'M'): (NO_BUTTON,
    SCROLL_DOWN, SHIFT_ALT), (81, 'M'): (NO_BUTTON, SCROLL_DOWN, CONTROL),
    (85, 'M'): (NO_BUTTON, SCROLL_DOWN, SHIFT_CONTROL), (89, 'M'): (
    NO_BUTTON, SCROLL_DOWN, ALT_CONTROL), (93, 'M'): (NO_BUTTON,
    SCROLL_DOWN, SHIFT_ALT_CONTROL)}
typical_mouse_events = {(32): (LEFT, MOUSE_DOWN, UNKNOWN_MODIFIER), (33): (
    MIDDLE, MOUSE_DOWN, UNKNOWN_MODIFIER), (34): (RIGHT, MOUSE_DOWN,
    UNKNOWN_MODIFIER), (35): (UNKNOWN_BUTTON, MOUSE_UP, UNKNOWN_MODIFIER),
    (64): (LEFT, MOUSE_MOVE, UNKNOWN_MODIFIER), (65): (MIDDLE, MOUSE_MOVE,
    UNKNOWN_MODIFIER), (66): (RIGHT, MOUSE_MOVE, UNKNOWN_MODIFIER), (67): (
    NO_BUTTON, MOUSE_MOVE, UNKNOWN_MODIFIER), (96): (NO_BUTTON, SCROLL_UP,
    UNKNOWN_MODIFIER), (97): (NO_BUTTON, SCROLL_DOWN, UNKNOWN_MODIFIER)}
urxvt_mouse_events = {(32): (UNKNOWN_BUTTON, MOUSE_DOWN, UNKNOWN_MODIFIER),
    (35): (UNKNOWN_BUTTON, MOUSE_UP, UNKNOWN_MODIFIER), (96): (NO_BUTTON,
    SCROLL_UP, UNKNOWN_MODIFIER), (97): (NO_BUTTON, SCROLL_DOWN,
    UNKNOWN_MODIFIER)}


def load_mouse_bindings() ->KeyBindings:
    """
    Key bindings, required for mouse support.
    (Mouse events enter through the key binding system.)
    """
    key_bindings = KeyBindings()

    @key_bindings.add(Keys.Any)
    def _(event: E) -> NotImplementedOrNone:
        """
        Catch mouse events.
        """
        if event.key_sequence[0].key == Keys.WindowsMouseEvent:
            return _handle_mouse_event(event, system="windows")
        elif event.key_sequence[0].key == Keys.VtMouseEvent:
            return _handle_mouse_event(event, system="vt")
        return NotImplemented

    return key_bindings

def _handle_mouse_event(event: E, system: str) -> None:
    """
    Handle mouse events for both Windows and VT systems.
    """
    # Get the parsed mouse event.
    mouse_event = event.key_sequence[0].data

    if system == "windows":
        # Windows systems
        x = mouse_event.position.x
        y = mouse_event.position.y
        button = mouse_event.button
        event_type = mouse_event.event_type
        modifiers = mouse_event.modifiers
    else:
        # VT systems
        x = mouse_event.x
        y = mouse_event.y
        button = mouse_event.button
        event_type = mouse_event.event_type
        modifiers = mouse_event.modifiers

    # Create a MouseEvent instance
    mouse_event = MouseEvent(position=Point(x=x, y=y),
                             event_type=event_type,
                             button=button,
                             modifiers=modifiers)

    # Call the mouse handler
    event.app.mouse_handlers.mouse_click(mouse_event)
