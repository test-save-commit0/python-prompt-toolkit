"""
Key bindings for auto suggestion (for fish-style auto suggestion).
"""
from __future__ import annotations
import re
from prompt_toolkit.application.current import get_app
from prompt_toolkit.filters import Condition, emacs_mode
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
__all__ = ['load_auto_suggest_bindings']
E = KeyPressEvent


def load_auto_suggest_bindings() ->KeyBindings:
    """
    Key bindings for accepting auto suggestion text.

    (This has to come after the Vi bindings, because they also have an
    implementation for the "right arrow", but we really want the suggestion
    binding when a suggestion is available.)
    """
    kb = KeyBindings()

    @Condition
    def suggestion_available() -> bool:
        app = get_app()
        return (
            app.current_buffer.suggestion is not None
            and app.current_buffer.document.is_cursor_at_the_end
        )

    @kb.add("right", filter=suggestion_available)
    @kb.add("c-e", filter=suggestion_available)
    @kb.add("c-f", filter=suggestion_available & emacs_mode)
    def _(event: E) -> None:
        """
        Accept the auto-suggestion.
        """
        b = event.current_buffer
        suggestion = b.suggestion

        if suggestion:
            b.insert_text(suggestion.text)

    @kb.add("c-right", filter=suggestion_available)
    def _(event: E) -> None:
        """
        Accept the next word of the auto-suggestion.
        """
        b = event.current_buffer
        suggestion = b.suggestion

        if suggestion:
            word_match = re.match(r"^\S+\s*", suggestion.text)
            if word_match:
                b.insert_text(word_match.group())

    return kb
