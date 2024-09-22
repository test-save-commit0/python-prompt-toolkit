from __future__ import annotations
from typing import Callable
from prompt_toolkit.eventloop import InputHook
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.input import DummyInput
from prompt_toolkit.output import DummyOutput
from .application import Application
__all__ = ['DummyApplication']


class DummyApplication(Application[None]):
    """
    When no :class:`.Application` is running,
    :func:`.get_app` will run an instance of this :class:`.DummyApplication` instead.
    """

    def __init__(self) ->None:
        super().__init__(output=DummyOutput(), input=DummyInput())
