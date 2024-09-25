from __future__ import annotations
import os
from enum import Enum
__all__ = ['ColorDepth']


class ColorDepth(str, Enum):
    """
    Possible color depth values for the output.
    """
    value: str
    DEPTH_1_BIT = 'DEPTH_1_BIT'
    DEPTH_4_BIT = 'DEPTH_4_BIT'
    DEPTH_8_BIT = 'DEPTH_8_BIT'
    DEPTH_24_BIT = 'DEPTH_24_BIT'
    MONOCHROME = DEPTH_1_BIT
    ANSI_COLORS_ONLY = DEPTH_4_BIT
    DEFAULT = DEPTH_8_BIT
    TRUE_COLOR = DEPTH_24_BIT

    @classmethod
    def from_env(cls) ->(ColorDepth | None):
        """
        Return the color depth if the $PROMPT_TOOLKIT_COLOR_DEPTH environment
        variable has been set.

        This is a way to enforce a certain color depth in all prompt_toolkit
        applications.
        """
        env_value = os.environ.get('PROMPT_TOOLKIT_COLOR_DEPTH')
        if env_value:
            try:
                return cls(env_value)
            except ValueError:
                # If the value is not a valid ColorDepth, return None
                return None
        return None

    @classmethod
    def default(cls) ->ColorDepth:
        """
        Return the default color depth for the default output.
        """
        # First, check if there's an environment variable set
        from_env = cls.from_env()
        if from_env is not None:
            return from_env

        # If no environment variable is set, return the DEFAULT value
        return cls.DEFAULT
