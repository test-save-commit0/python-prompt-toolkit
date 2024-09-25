from __future__ import annotations
from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Union
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding.vi_state import InputMode
if TYPE_CHECKING:
    from .application import Application
__all__ = ['CursorShape', 'CursorShapeConfig', 'SimpleCursorShapeConfig',
    'ModalCursorShapeConfig', 'DynamicCursorShapeConfig',
    'to_cursor_shape_config']


class CursorShape(Enum):
    _NEVER_CHANGE = '_NEVER_CHANGE'
    BLOCK = 'BLOCK'
    BEAM = 'BEAM'
    UNDERLINE = 'UNDERLINE'
    BLINKING_BLOCK = 'BLINKING_BLOCK'
    BLINKING_BEAM = 'BLINKING_BEAM'
    BLINKING_UNDERLINE = 'BLINKING_UNDERLINE'


class CursorShapeConfig(ABC):

    @abstractmethod
    def get_cursor_shape(self, application: Application[Any]) ->CursorShape:
        """
        Return the cursor shape to be used in the current state.
        """
        pass


AnyCursorShapeConfig = Union[CursorShape, CursorShapeConfig, None]


class SimpleCursorShapeConfig(CursorShapeConfig):
    """
    Always show the given cursor shape.
    """

    def __init__(self, cursor_shape: CursorShape=CursorShape._NEVER_CHANGE
        ) ->None:
        self.cursor_shape = cursor_shape

    def get_cursor_shape(self, application: Application[Any]) ->CursorShape:
        return self.cursor_shape


class ModalCursorShapeConfig(CursorShapeConfig):
    """
    Show cursor shape according to the current input mode.
    """

    def __init__(self, 
                 emacs: CursorShape = CursorShape.BEAM,
                 vi_insert: CursorShape = CursorShape.BEAM,
                 vi_navigation: CursorShape = CursorShape.BLOCK) -> None:
        self.emacs = emacs
        self.vi_insert = vi_insert
        self.vi_navigation = vi_navigation

    def get_cursor_shape(self, application: Application[Any]) -> CursorShape:
        if application.editing_mode == EditingMode.VI:
            if application.vi_state.input_mode == InputMode.INSERT:
                return self.vi_insert
            else:
                return self.vi_navigation
        else:
            return self.emacs


class DynamicCursorShapeConfig(CursorShapeConfig):

    def __init__(self, get_cursor_shape_config: Callable[[],
        AnyCursorShapeConfig]) ->None:
        self.get_cursor_shape_config = get_cursor_shape_config

    def get_cursor_shape(self, application: Application[Any]) -> CursorShape:
        config = self.get_cursor_shape_config()
        if isinstance(config, CursorShape):
            return config
        elif isinstance(config, CursorShapeConfig):
            return config.get_cursor_shape(application)
        else:
            return CursorShape._NEVER_CHANGE


def to_cursor_shape_config(value: AnyCursorShapeConfig) ->CursorShapeConfig:
    """
    Take a `CursorShape` instance or `CursorShapeConfig` and turn it into a
    `CursorShapeConfig`.
    """
    if isinstance(value, CursorShapeConfig):
        return value
    elif isinstance(value, CursorShape):
        return SimpleCursorShapeConfig(value)
    elif value is None:
        return SimpleCursorShapeConfig(CursorShape._NEVER_CHANGE)
    else:
        raise TypeError(f"Invalid cursor shape config: {value}")
