"""
File: state_coverage.py

Purpose:
    Stores raw and eligible action coverage information
    for one discovered application state.

Architecture:

Application State
        +
Exploration Memory
        +
Action Filter
        ↓
StateCoverage

Coverage Types:

    Raw Coverage
        Measures all actions discovered in the UI.

    Eligible Coverage
        Measures only actions allowed by the current
        exploration policy.

Why Both Metrics Are Required:
    Some UI controls may intentionally be blocked.

    Examples:

        - Close
        - Minimize
        - Maximize
        - destructive system actions

    These actions should remain visible in raw coverage,
    but they should not reduce the useful exploration
    coverage percentage.
"""

from dataclasses import dataclass


@dataclass
class StateCoverage:
    """
    Coverage information for one graph state.

    Raw metrics describe all discovered UI actions.

    Eligible metrics describe only actions that the
    exploration policy allows.
    """

    state_id: str

    state_hash: str

    depth: int

    # =====================================================
    # Raw action coverage
    # =====================================================

    total_actions: int

    explored_actions: int

    unexplored_actions: int

    coverage_percentage: float

    # =====================================================
    # Eligible action coverage
    # =====================================================

    eligible_total_actions: int

    eligible_explored_actions: int

    eligible_unexplored_actions: int

    eligible_coverage_percentage: float

    @property
    def is_fully_explored(
        self
    ) -> bool:
        """
        Return True when every raw discovered action
        has been explored.
        """

        return (
            self.unexplored_actions
            == 0
        )

    @property
    def is_unexplored(
        self
    ) -> bool:
        """
        Return True when the state contains raw actions
        but none have been explored.
        """

        return (
            self.total_actions > 0
            and
            self.explored_actions == 0
        )

    @property
    def is_partially_explored(
        self
    ) -> bool:
        """
        Return True when some raw actions have been
        explored and some remain.
        """

        return (
            self.explored_actions > 0
            and
            self.unexplored_actions > 0
        )

    @property
    def is_fully_eligible_explored(
        self
    ) -> bool:
        """
        Return True when every eligible action has
        been explored.

        A state with zero eligible actions is also
        considered complete from the exploration
        policy's perspective.
        """

        return (
            self.eligible_unexplored_actions
            == 0
        )

    @property
    def is_eligible_unexplored(
        self
    ) -> bool:
        """
        Return True when eligible actions exist but
        none have been explored.
        """

        return (
            self.eligible_total_actions > 0
            and
            self.eligible_explored_actions == 0
        )

    @property
    def is_eligible_partially_explored(
        self
    ) -> bool:
        """
        Return True when some eligible actions have
        been explored and some remain.
        """

        return (
            self.eligible_explored_actions > 0
            and
            self.eligible_unexplored_actions > 0
        )