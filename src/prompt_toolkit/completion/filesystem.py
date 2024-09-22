from __future__ import annotations
import os
from typing import Callable, Iterable
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
__all__ = ['PathCompleter', 'ExecutableCompleter']


class PathCompleter(Completer):
    """
    Complete for Path variables.

    :param get_paths: Callable which returns a list of directories to look into
                      when the user enters a relative path.
    :param file_filter: Callable which takes a filename and returns whether
                        this file should show up in the completion. ``None``
                        when no filtering has to be done.
    :param min_input_len: Don't do autocompletion when the input string is shorter.
    """

    def __init__(self, only_directories: bool=False, get_paths: (Callable[[
        ], list[str]] | None)=None, file_filter: (Callable[[str], bool] |
        None)=None, min_input_len: int=0, expanduser: bool=False) ->None:
        self.only_directories = only_directories
        self.get_paths = get_paths or (lambda : ['.'])
        self.file_filter = file_filter or (lambda _: True)
        self.min_input_len = min_input_len
        self.expanduser = expanduser


class ExecutableCompleter(PathCompleter):
    """
    Complete only executable files in the current path.
    """

    def __init__(self) ->None:
        super().__init__(only_directories=False, min_input_len=1, get_paths
            =lambda : os.environ.get('PATH', '').split(os.pathsep),
            file_filter=lambda name: os.access(name, os.X_OK), expanduser=True)
