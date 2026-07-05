"""
Abstract interface for exploration target ranking strategies.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from agent.strategy.exploration_target import ExplorationTarget


class ExplorationStrategy(ABC):
    """
    Base interface for all exploration ranking strategies.

    Responsibilities:
        - Receive already-valid exploration candidates.
        - Rank those candidates.
        - Return a new ordered list.

    Non-responsibilities:
        - Coverage calculation.
        - Action filtering.
        - Depth-limit enforcement.
        - State expandability checks.

    Those concerns belong to the CoverageEngine and
    ExplorationTargetSelector.
    """

    @abstractmethod
    def rank_targets(
        self,
        candidates: Sequence[ExplorationTarget],
    ) -> list[ExplorationTarget]:
        """
        Rank exploration candidates from highest to lowest priority.

        Args:
            candidates:
                Valid exploration targets that have already passed all
                execution constraints.

        Returns:
            A newly ordered list where index 0 is the best next target.
        """
        raise NotImplementedError