from __future__ import annotations
from .key_processor import KeyPress
__all__ = ['EmacsState']


class EmacsState:
    """
    Mutable class to hold Emacs specific state.
    """

    def __init__(self) ->None:
        self.macro: list[KeyPress] | None = []
        self.current_recording: list[KeyPress] | None = None

    @property
    def is_recording(self) ->bool:
        """Tell whether we are recording a macro."""
        pass

    def start_macro(self) ->None:
        """Start recording macro."""
        pass

    def end_macro(self) ->None:
        """End recording macro."""
        pass
