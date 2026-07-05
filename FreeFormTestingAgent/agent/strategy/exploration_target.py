"""
Data model representing a state selected for future exploration.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ExplorationTarget:
    """
    Represents one state that is eligible for additional exploration.

    An ExplorationTarget is not the application state itself. It is a compact
    decision object containing only the information needed by exploration
    strategies.

    Attributes:
        state_id:
            Unique graph identifier of the application state.

        state_hash:
            Deterministic hash of the application state.

        depth:
            Shortest known graph depth of the state.

        unexplored_eligible_actions:
            Number of actions that:
                1. Exist in the state.
                2. Are allowed by the ActionFilter.
                3. Have not yet been executed from this state.

        priority_score:
            Optional numeric score assigned by a strategy.

            V1 ranking is tuple-based and deterministic, so this value is
            currently informational. Future strategies may use it for
            heuristic or AI-assisted scoring.

        selection_reason:
            Human-readable explanation describing why the state is a useful
            exploration target.
    """

    state_id: str
    state_hash: str
    depth: int
    unexplored_eligible_actions: int
    priority_score: float = 0.0
    selection_reason: str = ""