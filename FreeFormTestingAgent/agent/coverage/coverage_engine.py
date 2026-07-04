"""
File: coverage_engine.py

Purpose:
    Calculate raw and eligible exploration coverage.

Architecture:

StateGraph
    +
ExplorationMemory
    +
ActionFilter
        ↓
CoverageEngine
        ↓
CoverageReport

Coverage Types:

    Raw Coverage
        All actions discovered in ApplicationState.

    Eligible Coverage
        Only actions allowed by the exploration policy.

Primary Use:
    Raw coverage describes the complete discovered UI.

    Eligible coverage describes how much useful,
    permitted exploration has been completed.
"""

from agent.coverage.state_coverage import (
    StateCoverage
)

from agent.coverage.coverage_report import (
    CoverageReport
)

from agent.explorer.default_action_filter import (
    DefaultActionFilter
)


class CoverageEngine:
    """
    Calculates exploration coverage.

    Responsibilities:
        - Calculate raw per-state coverage.
        - Calculate eligible per-state coverage.
        - Calculate global coverage.
        - Find states with remaining eligible actions.
        - Identify completed exploration areas.
    """

    def __init__(
        self,
        graph,
        memory,
        action_filter=None
    ):
        """
        Initialize the Coverage Engine.

        Parameters
        ----------
        graph:
            StateGraph containing discovered states.

        memory:
            ExplorationMemory containing executed actions.

        action_filter:
            Policy used to determine which actions are
            eligible for exploration.

            When not provided, DefaultActionFilter is used.
        """

        self.graph = graph

        self.memory = memory

        self.action_filter = (
            action_filter
            or
            DefaultActionFilter()
        )

    def _calculate_percentage(
        self,
        explored: int,
        total: int
    ) -> float:
        """
        Calculate a safe coverage percentage.

        A collection containing zero actions is considered
        100% covered because nothing remains to explore.
        """

        if total == 0:
            return 100.0

        percentage = (
            explored
            /
            total
            *
            100
        )

        return round(
            percentage,
            2
        )

    def calculate_state_coverage(
        self,
        state_id: str
    ) -> StateCoverage | None:
        """
        Calculate raw and eligible coverage for one state.
        """

        node = self.graph.get_state(
            state_id
        )

        if node is None:
            return None

        state = node.state

        # =====================================================
        # RAW ACTIONS
        #
        # Every action discovered in the UI.
        # =====================================================

        raw_actions = (
            state.available_actions
        )

        raw_unexplored_actions = (
            self.memory
            .get_unexplored_actions(
                state.state_hash,
                raw_actions
            )
        )

        total_actions = len(
            raw_actions
        )

        unexplored_actions = len(
            raw_unexplored_actions
        )

        explored_actions = (
            total_actions
            -
            unexplored_actions
        )

        raw_coverage_percentage = (
            self._calculate_percentage(
                explored_actions,
                total_actions
            )
        )

        # =====================================================
        # ELIGIBLE ACTIONS
        #
        # Only actions permitted by the exploration policy.
        # =====================================================

        eligible_actions = [
            action

            for action
            in raw_actions

            if self.action_filter.allow(
                action
            )
        ]

        eligible_unexplored = (
            self.memory
            .get_unexplored_actions(
                state.state_hash,
                eligible_actions
            )
        )

        eligible_total_actions = len(
            eligible_actions
        )

        eligible_unexplored_actions = len(
            eligible_unexplored
        )

        eligible_explored_actions = (
            eligible_total_actions
            -
            eligible_unexplored_actions
        )

        eligible_coverage_percentage = (
            self._calculate_percentage(
                eligible_explored_actions,
                eligible_total_actions
            )
        )

        return StateCoverage(
            state_id=state_id,
            state_hash=state.state_hash,
            depth=node.depth,

            total_actions=total_actions,
            explored_actions=explored_actions,
            unexplored_actions=unexplored_actions,
            coverage_percentage=(
                raw_coverage_percentage
            ),

            eligible_total_actions=(
                eligible_total_actions
            ),
            eligible_explored_actions=(
                eligible_explored_actions
            ),
            eligible_unexplored_actions=(
                eligible_unexplored_actions
            ),
            eligible_coverage_percentage=(
                eligible_coverage_percentage
            )
        )

    def calculate_report(
        self
    ) -> CoverageReport:
        """
        Calculate raw and eligible coverage for the
        complete graph.
        """

        state_reports = []

        # =====================================================
        # Raw counters
        # =====================================================

        total_actions = 0

        explored_actions = 0

        unexplored_actions = 0

        fully_explored_states = 0

        partially_explored_states = 0

        unexplored_states = 0

        # =====================================================
        # Eligible counters
        # =====================================================

        eligible_total_actions = 0

        eligible_explored_actions = 0

        eligible_unexplored_actions = 0

        fully_eligible_explored_states = 0

        partially_eligible_explored_states = 0

        eligible_unexplored_states = 0

        # =====================================================
        # Analyze every graph state
        # =====================================================

        for state_id in self.graph.states:

            coverage = (
                self.calculate_state_coverage(
                    state_id
                )
            )

            if coverage is None:
                continue

            state_reports.append(
                coverage
            )

            # =================================================
            # Aggregate raw metrics
            # =================================================

            total_actions += (
                coverage.total_actions
            )

            explored_actions += (
                coverage.explored_actions
            )

            unexplored_actions += (
                coverage.unexplored_actions
            )

            if coverage.is_fully_explored:

                fully_explored_states += 1

            elif coverage.is_unexplored:

                unexplored_states += 1

            elif coverage.is_partially_explored:

                partially_explored_states += 1

            # =================================================
            # Aggregate eligible metrics
            # =================================================

            eligible_total_actions += (
                coverage.eligible_total_actions
            )

            eligible_explored_actions += (
                coverage.eligible_explored_actions
            )

            eligible_unexplored_actions += (
                coverage.eligible_unexplored_actions
            )

            if (
                coverage
                .is_fully_eligible_explored
            ):

                fully_eligible_explored_states += 1

            elif (
                coverage
                .is_eligible_unexplored
            ):

                eligible_unexplored_states += 1

            elif (
                coverage
                .is_eligible_partially_explored
            ):

                partially_eligible_explored_states += 1

        # =====================================================
        # Calculate global percentages
        # =====================================================

        raw_percentage = (
            self._calculate_percentage(
                explored_actions,
                total_actions
            )
        )

        eligible_percentage = (
            self._calculate_percentage(
                eligible_explored_actions,
                eligible_total_actions
            )
        )

        return CoverageReport(
            total_states=len(
                self.graph.states
            ),

            total_actions=total_actions,
            explored_actions=explored_actions,
            unexplored_actions=unexplored_actions,
            action_coverage_percentage=(
                raw_percentage
            ),

            fully_explored_states=(
                fully_explored_states
            ),
            partially_explored_states=(
                partially_explored_states
            ),
            unexplored_states=(
                unexplored_states
            ),

            eligible_total_actions=(
                eligible_total_actions
            ),
            eligible_explored_actions=(
                eligible_explored_actions
            ),
            eligible_unexplored_actions=(
                eligible_unexplored_actions
            ),
            eligible_action_coverage_percentage=(
                eligible_percentage
            ),

            fully_eligible_explored_states=(
                fully_eligible_explored_states
            ),
            partially_eligible_explored_states=(
                partially_eligible_explored_states
            ),
            eligible_unexplored_states=(
                eligible_unexplored_states
            ),

            state_coverage=state_reports
        )

    def get_states_with_unexplored_actions(
        self
    ) -> list[StateCoverage]:
        """
        Return states containing any raw unexplored actions.
        """

        states = []

        for state_id in self.graph.states:

            coverage = (
                self.calculate_state_coverage(
                    state_id
                )
            )

            if (
                coverage is not None
                and
                coverage.unexplored_actions > 0
            ):

                states.append(
                    coverage
                )

        return states

    def get_states_with_unexplored_eligible_actions(
        self
    ) -> list[StateCoverage]:
        """
        Return states containing actions that:

            1. Are allowed by the exploration policy.
            2. Have not yet been executed.

        This is the primary query for future exploration
        strategies and AI planners.
        """

        states = []

        for state_id in self.graph.states:

            coverage = (
                self.calculate_state_coverage(
                    state_id
                )
            )

            if (
                coverage is not None
                and
                coverage.eligible_unexplored_actions > 0
            ):

                states.append(
                    coverage
                )

        return states

    def get_fully_explored_states(
        self
    ) -> list[StateCoverage]:
        """
        Return states with complete raw coverage.
        """

        states = []

        for state_id in self.graph.states:

            coverage = (
                self.calculate_state_coverage(
                    state_id
                )
            )

            if (
                coverage is not None
                and
                coverage.is_fully_explored
            ):

                states.append(
                    coverage
                )

        return states

    def get_fully_eligible_explored_states(
        self
    ) -> list[StateCoverage]:
        """
        Return states with complete eligible coverage.
        """

        states = []

        for state_id in self.graph.states:

            coverage = (
                self.calculate_state_coverage(
                    state_id
                )
            )

            if (
                coverage is not None
                and
                coverage.is_fully_eligible_explored
            ):

                states.append(
                    coverage
                )

        return states