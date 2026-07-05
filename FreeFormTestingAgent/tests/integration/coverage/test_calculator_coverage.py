"""
File: test_calculator_coverage.py

Purpose:
    Verify that the Coverage Engine works with a real
    replay-aware BFS exploration session.

Integration Flow:

    Real Calculator
            ↓
    BFSExplorer
            ↓
    StateGraph + ExplorationMemory
            ↓
    CoverageEngine
            ↓
    Raw + Eligible CoverageReport

What This Test Proves:
    1. BFS exploration creates real graph knowledge.
    2. ExplorationMemory records executed actions.
    3. CoverageEngine reads the graph and memory correctly.
    4. Raw coverage includes all discovered UI actions.
    5. Eligible coverage includes only policy-allowed actions.
    6. The engine can identify states where useful
       exploration can continue.
"""

from tests.fixtures.calculator_fixture import (
    CalculatorFixture
)

from agent.executor.action_executor import (
    ActionExecutor
)

from agent.memory.exploration_memory import (
    ExplorationMemory
)

from agent.explorer.bfs_explorer import (
    BFSExplorer
)

from agent.explorer.action_filter import (
    ActionFilter
)

from agent.explorer.exploration_limits import (
    ExplorationLimits
)

from agent.replay.replay_engine import (
    ReplayEngine
)

from agent.coverage.coverage_engine import (
    CoverageEngine
)

from core.graph.state_graph import (
    StateGraph
)


class CoverageTestActionFilter(
    ActionFilter
):
    """
    Controlled exploration policy for the integration test.

    Only these Calculator actions are eligible:

        7
        8
        +
        =

    Why Use a Controlled Filter?
    ----------------------------
    A small action space makes the resulting coverage report
    deterministic and easy to inspect.
    """

    ALLOWED_ACTIONS = {
        "num7Button",
        "num8Button",
        "plusButton",
        "equalButton",
    }

    def allow(
        self,
        action
    ) -> bool:
        """
        Return True only for actions intentionally included
        in this coverage test.
        """

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
        )


def print_coverage_report(
    report
):
    """
    Print global and per-state coverage information.

    This output is intentionally detailed because the test
    also acts as an integration diagnostic.
    """

    print()
    print(
        "======================================"
    )

    print(
        "COVERAGE REPORT"
    )

    print(
        "======================================"
    )

    print()
    print(
        "Total States:",
        report.total_states
    )

    # =====================================================
    # Raw coverage
    # =====================================================

    print()
    print(
        "===== RAW COVERAGE ====="
    )

    print(
        "Total Actions:",
        report.total_actions
    )

    print(
        "Explored Actions:",
        report.explored_actions
    )

    print(
        "Unexplored Actions:",
        report.unexplored_actions
    )

    print(
        "Coverage:",
        f"{report.action_coverage_percentage}%"
    )

    print(
        "Fully Explored States:",
        report.fully_explored_states
    )

    print(
        "Partially Explored States:",
        report.partially_explored_states
    )

    print(
        "Unexplored States:",
        report.unexplored_states
    )

    # =====================================================
    # Eligible coverage
    # =====================================================

    print()
    print(
        "===== ELIGIBLE COVERAGE ====="
    )

    print(
        "Eligible Actions:",
        report.eligible_total_actions
    )

    print(
        "Explored Eligible Actions:",
        report.eligible_explored_actions
    )

    print(
        "Unexplored Eligible Actions:",
        report.eligible_unexplored_actions
    )

    print(
        "Eligible Coverage:",
        f"{report.eligible_action_coverage_percentage}%"
    )

    print(
        "Fully Eligible Explored States:",
        report.fully_eligible_explored_states
    )

    print(
        "Partially Eligible Explored States:",
        report.partially_eligible_explored_states
    )

    print(
        "Eligible Unexplored States:",
        report.eligible_unexplored_states
    )

    # =====================================================
    # Per-state coverage
    # =====================================================

    print()
    print(
        "===== PER-STATE COVERAGE ====="
    )

    for coverage in report.state_coverage:

        print()

        print(
            "State:",
            coverage.state_id
        )

        print(
            "Depth:",
            coverage.depth
        )

        print(
            "Raw:",
            (
                f"{coverage.explored_actions}"
                f"/"
                f"{coverage.total_actions}"
                f" "
                f"({coverage.coverage_percentage}%)"
            )
        )

        print(
            "Eligible:",
            (
                f"{coverage.eligible_explored_actions}"
                f"/"
                f"{coverage.eligible_total_actions}"
                f" "
                f"({coverage.eligible_coverage_percentage}%)"
            )
        )


def test_calculator_coverage():
    """
    Run controlled Calculator exploration and analyze
    the resulting coverage.
    """

    with CalculatorFixture() as (
        ui,
        window
    ):

        # =====================================================
        # STEP 1
        # Create shared exploration components
        # =====================================================

        graph = StateGraph()

        memory = ExplorationMemory()

        executor = ActionExecutor()

        action_filter = (
            CoverageTestActionFilter()
        )

        replay_engine = ReplayEngine(
            ui,
            executor,
            graph
        )

        limits = ExplorationLimits(
            max_states=20,
            max_actions=12,
            max_transitions=20,
            max_depth=2,
            max_duration=120.0,
            max_failures=10
        )

        # =====================================================
        # STEP 2
        # Create BFS Explorer
        #
        # Important:
        # The same action_filter instance will later be passed
        # to CoverageEngine.
        # =====================================================

        explorer = BFSExplorer(
            ui=ui,
            executor=executor,
            graph=graph,
            memory=memory,
            replay_engine=replay_engine,
            executable="calc.exe",
            window_title="Calculator",
            action_filter=action_filter,
            limits=limits
        )

        # =====================================================
        # STEP 3
        # Explore the real application
        # =====================================================

        result = explorer.explore(
            window
        )

        print()
        print(
            "===== EXPLORATION RESULT ====="
        )

        print(
            result
        )

        # =====================================================
        # STEP 4
        # Analyze the discovered graph
        # =====================================================

        coverage_engine = CoverageEngine(
            graph=graph,
            memory=memory,
            action_filter=action_filter
        )

        report = (
            coverage_engine.calculate_report()
        )

        # =====================================================
        # STEP 5
        # Print diagnostic report
        # =====================================================

        print_coverage_report(
            report
        )

        # =====================================================
        # STEP 6
        # Basic integration assertions
        # =====================================================

        assert report.total_states > 0, (
            "Coverage report contains no states."
        )

        assert report.total_actions > 0, (
            "No raw UI actions were discovered."
        )

        assert (
            report.eligible_total_actions
            > 0
        ), (
            "No eligible actions were discovered."
        )

        assert (
            report.explored_actions
            > 0
        ), (
            "ExplorationMemory did not record "
            "executed actions."
        )

        assert (
            report.eligible_explored_actions
            > 0
        ), (
            "No eligible actions were recorded "
            "as explored."
        )

        # =====================================================
        # STEP 7
        # Eligible actions must be a subset of raw actions
        # =====================================================

        assert (
            report.eligible_total_actions
            <=
            report.total_actions
        ), (
            "Eligible actions cannot exceed "
            "all discovered actions."
        )

        assert (
            report.eligible_explored_actions
            <=
            report.explored_actions
        ), (
            "Explored eligible actions cannot exceed "
            "all explored actions."
        )

        # =====================================================
        # STEP 8
        # Validate percentage boundaries
        # =====================================================

        assert (
            0.0
            <=
            report.action_coverage_percentage
            <=
            100.0
        )

        assert (
            0.0
            <=
            report.eligible_action_coverage_percentage
            <=
            100.0
        )

        # =====================================================
        # STEP 9
        # Validate per-state arithmetic
        # =====================================================

        for coverage in report.state_coverage:

            assert (
                coverage.explored_actions
                +
                coverage.unexplored_actions
                ==
                coverage.total_actions
            )

            assert (
                coverage.eligible_explored_actions
                +
                coverage.eligible_unexplored_actions
                ==
                coverage.eligible_total_actions
            )

        # =====================================================
        # STEP 10
        # Query remaining useful exploration work
        # =====================================================

        remaining_states = (
            coverage_engine
            .get_states_with_unexplored_eligible_actions()
        )

        print()
        print(
            "===== STATES WITH REMAINING "
            "ELIGIBLE ACTIONS ====="
        )

        for coverage in remaining_states:

            print(
                coverage.state_id,
                "| Depth:",
                coverage.depth,
                "| Remaining:",
                coverage.eligible_unexplored_actions
            )

        print()
        print(
            "CALCULATOR COVERAGE TEST PASSED"
        )


if __name__ == "__main__":

    test_calculator_coverage()