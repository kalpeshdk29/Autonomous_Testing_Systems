"""
Deterministic shallowest-first exploration strategy.
"""

from typing import Sequence

from agent.strategy.exploration_strategy import ExplorationStrategy
from agent.strategy.exploration_target import ExplorationTarget


class ShallowestFirstStrategy(ExplorationStrategy):
    """
    Rank valid exploration targets using deterministic V1 rules.

    Ranking priority:

        1. Lowest depth first.
        2. Most unexplored eligible actions first.
        3. State ID alphabetically as the final deterministic tie-breaker.

    Example:

        State A:
            depth = 1
            unexplored eligible actions = 2

        State B:
            depth = 1
            unexplored eligible actions = 5

        State C:
            depth = 2
            unexplored eligible actions = 10

        Result:
            B
            A
            C

    The strategy intentionally does not enforce max_depth.

    Invalid or non-expandable states must be removed by the
    ExplorationTargetSelector before this strategy is called.
    """

    def rank_targets(
        self,
        candidates: Sequence[ExplorationTarget],
    ) -> list[ExplorationTarget]:
        """
        Return candidates ordered from highest to lowest exploration priority.

        Ranking key:

            (
                depth ascending,
                unexplored eligible actions descending,
                state_id ascending,
            )

        The original candidate collection is not modified.

        Args:
            candidates:
                ExplorationTarget objects that have already passed all
                selector constraints.

        Returns:
            A new list ordered from highest to lowest priority.
        """

        return sorted(
            candidates,
            key=lambda target: (
                target.depth,
                -target.unexplored_eligible_actions,
                target.state_id,
            ),
        )