"""
Abstract interface for action-ranking strategies.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from core.models.action import Action


class ActionSelectionStrategy(ABC):
    """
    Base interface for all action-selection strategies.

    Responsibilities:
        - Receive already-valid action candidates.
        - Rank those candidates.
        - Return a new ordered list.

    Non-responsibilities:
        - Checking ExplorationMemory.
        - Applying ActionFilter.
        - Locating application states.
        - Executing actions.

    Those responsibilities belong to other framework components.
    """

    @abstractmethod
    def rank_actions(
        self,
        candidates: Sequence[Action],
    ) -> list[Action]:
        """
        Rank valid action candidates.

        Args:
            candidates:
                Actions that have already passed memory and
                eligibility filtering.

        Returns:
            A new list where index 0 is the preferred next action.
        """

        raise NotImplementedError