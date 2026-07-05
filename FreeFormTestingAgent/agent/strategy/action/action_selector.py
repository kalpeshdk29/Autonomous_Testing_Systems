"""
Action candidate selection and ranking orchestration.
"""

from typing import Optional, Sequence

from core.models.action import Action

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.explorer.action_filter import (
    ActionFilter,
)

from agent.strategy.action.action_selection_strategy import (
    ActionSelectionStrategy,
)


class ActionSelector:
    """
    Select the next unexplored eligible action for a state.

    Processing pipeline:

        State Hash + Available Actions
                ↓
        ExplorationMemory
                ↓
        Remove Already Executed Actions
                ↓
        ActionFilter
                ↓
        Remove Blocked Actions
                ↓
        ActionSelectionStrategy
                ↓
        Ranked Actions
                ↓
        Best Next Action

    Responsibility Separation
    -------------------------

    ExplorationMemory:
        Knows whether an action was already executed.

    ActionFilter:
        Knows whether an action is allowed.

    ActionSelector:
        Builds the valid candidate set.

    ActionSelectionStrategy:
        Ranks valid candidates.
    """

    def __init__(
        self,
        memory: ExplorationMemory,
        action_filter: ActionFilter,
        strategy: ActionSelectionStrategy,
    ) -> None:
        """
        Initialize the action selector.

        Args:
            memory:
                Existing ExplorationMemory instance.

            action_filter:
                Current action eligibility policy.

            strategy:
                Strategy used to rank valid actions.
        """

        self.memory = memory
        self.action_filter = action_filter
        self.strategy = strategy

    def get_candidates(
        self,
        state_hash: str,
        actions: Sequence[Action],
    ) -> list[Action]:
        """
        Return actions that are both unexplored and eligible.

        An action becomes a candidate only when:

            1. It has not already been executed from this state.
            2. It is allowed by the current ActionFilter.

        Args:
            state_hash:
                Hash of the state being explored.

            actions:
                Actions currently available from that state.

        Returns:
            Valid, unranked action candidates.
        """

        unexplored_actions = (
            self.memory.get_unexplored_actions(
                state_hash,
                actions,
            )
        )

        candidates = []

        for action in unexplored_actions:

            if self.action_filter.allow(action):

                candidates.append(
                    action
                )

        return candidates

    def rank_actions(
        self,
        state_hash: str,
        actions: Sequence[Action],
    ) -> list[Action]:
        """
        Return all valid actions ranked by the configured strategy.
        """

        candidates = self.get_candidates(
            state_hash,
            actions,
        )

        return self.strategy.rank_actions(
            candidates
        )

    def select_next_action(
        self,
        state_hash: str,
        actions: Sequence[Action],
    ) -> Optional[Action]:
        """
        Select the highest-ranked valid action.

        Returns:
            The best next Action.

            None when no unexplored eligible action remains.
        """

        ranked_actions = self.rank_actions(
            state_hash,
            actions,
        )

        if not ranked_actions:
            return None

        return ranked_actions[0]