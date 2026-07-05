"""
Deterministic V1 action-ranking strategy.
"""

from typing import Sequence

from core.models.action import Action

from agent.strategy.action.action_selection_strategy import (
    ActionSelectionStrategy,
)


class DeterministicActionStrategy(
    ActionSelectionStrategy
):
    """
    Rank valid actions using stable deterministic rules.

    V1 ranking:

        1. Action type value ascending.
        2. Action target ascending.
        3. Action value ascending.

    Why No Semantic Priority Yet?
    -----------------------------
    We deliberately avoid assuming that CLICK is always more useful than
    TEXT_INPUT, KEY_PRESS, or another action type.

    Such priorities belong to future strategies.

    The purpose of V1 is simply to guarantee:

        - repeatability
        - predictability
        - stable tests
        - deterministic exploration
    """

    def rank_actions(
        self,
        candidates: Sequence[Action],
    ) -> list[Action]:
        """
        Return actions in deterministic order.

        The original candidate sequence is never modified.
        """

        return sorted(
            candidates,
            key=lambda action: (
                action.action_type.value,
                action.target,
                action.value or "",
            ),
        )