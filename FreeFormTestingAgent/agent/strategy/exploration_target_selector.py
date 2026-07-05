"""
Exploration target selection orchestration.

This module connects coverage information with execution constraints
and exploration ranking strategies.
"""

from typing import Optional

from agent.strategy.exploration_strategy import (
    ExplorationStrategy,
)

from agent.strategy.exploration_target import (
    ExplorationTarget,
)


class ExplorationTargetSelector:
    """
    Convert coverage information into ranked, executable
    exploration targets.

    Processing pipeline:

        CoverageEngine
            ↓
        States with unexplored eligible actions
            ↓
        Constraint filtering
            ↓
        ExplorationTarget objects
            ↓
        ExplorationStrategy
            ↓
        Ranked targets
            ↓
        Best next target

    Important depth semantics:

        If max_depth = 2:

            depth 0 -> expandable
            depth 1 -> expandable
            depth 2 -> not expandable

        Therefore:

            state_depth < max_depth

        must be true for a state to become an exploration
        candidate.
    """

    def __init__(
        self,
        coverage_engine,
        strategy: ExplorationStrategy,
        max_depth: Optional[int] = None,
    ) -> None:
        """
        Initialize the selector.

        Args:
            coverage_engine:
                Existing CoverageEngine instance.

            strategy:
                Ranking strategy used after constraint filtering.

            max_depth:
                Maximum discovery depth allowed by exploration.

                None means there is no depth restriction.
        """

        self.coverage_engine = coverage_engine
        self.strategy = strategy
        self.max_depth = max_depth

    def get_candidates(
        self,
    ) -> list[ExplorationTarget]:
        """
        Build valid exploration candidates.

        A state becomes a candidate only when:

            1. It has unexplored eligible actions.
            2. It is still expandable under max_depth.

        CoverageEngine is responsible for determining which
        states contain remaining eligible work.

        ExplorationTargetSelector is responsible for determining
        whether those states can currently be expanded.

        Returns:
            Valid, unranked ExplorationTarget objects.
        """

        state_coverages = (
            self.coverage_engine
            .get_states_with_unexplored_eligible_actions()
        )

        candidates: list[ExplorationTarget] = []

        for state_coverage in state_coverages:

            # A state at max_depth may exist in the graph and may
            # still contain unexplored eligible actions.
            #
            # However, expanding it would create states beyond the
            # configured exploration boundary.
            if not self._is_expandable(
                state_coverage.depth
            ):
                continue

            candidates.append(
                ExplorationTarget(
                    state_id=state_coverage.state_id,
                    state_hash=state_coverage.state_hash,
                    depth=state_coverage.depth,
                    unexplored_eligible_actions=(
                        state_coverage
                        .eligible_unexplored_actions
                    ),
                    priority_score=0.0,
                    selection_reason=(
                        "State has "
                        f"{state_coverage.eligible_unexplored_actions} "
                        "unexplored eligible action(s) at depth "
                        f"{state_coverage.depth}."
                    ),
                )
            )

        return candidates

    def rank_targets(
        self,
    ) -> list[ExplorationTarget]:
        """
        Return all valid candidates ranked by the configured
        exploration strategy.
        """

        candidates = self.get_candidates()

        return self.strategy.rank_targets(
            candidates
        )

    def select_next_target(
        self,
    ) -> Optional[ExplorationTarget]:
        """
        Select the highest-priority exploration target.

        Returns:
            The best ExplorationTarget.

            None when no expandable state has remaining
            eligible work.
        """

        ranked_targets = self.rank_targets()

        if not ranked_targets:
            return None

        return ranked_targets[0]

    def _is_expandable(
        self,
        depth: int,
    ) -> bool:
        """
        Determine whether a state may still be expanded.

        Rules:

            max_depth is None:
                Every depth is expandable.

            max_depth = N:
                Only states where depth < N are expandable.
        """

        if self.max_depth is None:
            return True

        return depth < self.max_depth