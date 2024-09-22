from __future__ import annotations
from enum import Enum


class EditingMode(Enum):
    VI = 'VI'
    EMACS = 'EMACS'


SEARCH_BUFFER = 'SEARCH_BUFFER'
DEFAULT_BUFFER = 'DEFAULT_BUFFER'
SYSTEM_BUFFER = 'SYSTEM_BUFFER'
