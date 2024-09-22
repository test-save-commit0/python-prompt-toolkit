from __future__ import annotations
import pyperclip
from prompt_toolkit.selection import SelectionType
from .base import Clipboard, ClipboardData
__all__ = ['PyperclipClipboard']


class PyperclipClipboard(Clipboard):
    """
    Clipboard that synchronizes with the Windows/Mac/Linux system clipboard,
    using the pyperclip module.
    """

    def __init__(self) ->None:
        self._data: ClipboardData | None = None
