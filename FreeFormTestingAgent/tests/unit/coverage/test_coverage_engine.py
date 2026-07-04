"""
File: test_coverage_engine.py

Purpose:
    Verify CoverageEngine calculations using a
    controlled in-memory graph.

Test Structure:

    S0
        Actions:
            A → explored
            B → explored
            C → unexplored

        Coverage:
            2 / 3
            66.67%

    S1
        Actions:
            D → unexplored
            E → unexplored

        Coverage:
            0 / 2
            0%

    S2
        Actions:
            F → explored

        Coverage:
            1 / 1
            100%

Global:

    Total Actions:      6
    Explored Actions:   3
    Unexplored Actions: 3

    Coverage: 50%

State Classification:

    Fully Explored:     1
    Partially Explored: 1
    Unexplored:         1
"""

from core.graph.state_graph import (
    StateGraph
)

from core.models.state import (
    ApplicationState
)

from core.models.action import (
    Action
)

from core.models.action import (
    ActionType
)

from agent.memory.exploration_memory import (
    ExplorationMemory
)

from agent.coverage.coverage_engine import (
    CoverageEngine
)


def create_action(
    target: str
) -> Action:
    """
    Create a simple CLICK action for testing.
    """

    return Action(
        action_type=ActionType.CLICK,
        target=target
    )


def create_state(
    state_hash: str,
    actions: list[Action]
) -> ApplicationState:
    """
    Create a controlled application state.
    """

    return ApplicationState(
        window_title="Test Application",
        state_hash=state_hash,
        available_actions=actions
    )


def create_test_environment():
    """
    Create the controlled graph and exploration memory.

    Returns
    -------
    tuple:
        graph,
        memory,
        state IDs
    """

    graph = StateGraph()

    memory = ExplorationMemory()

    # =====================================================
    # S0
    #
    # A → explored
    # B → explored
    # C → unexplored
    # =====================================================

    state0 = create_state(
        "state-0-hash",
        [
            create_action("A"),
            create_action("B"),
            create_action("C"),
        ]
    )

    state0_id = graph.add_state(
        state0,
        depth=0
    )

    memory.mark_executed(
        state0.state_hash,
        "A"
    )

    memory.mark_executed(
        state0.state_hash,
        "B"
    )

    # =====================================================
    # S1
    #
    # D → unexplored
    # E → unexplored
    # =====================================================

    state1 = create_state(
        "state-1-hash",
        [
            create_action("D"),
            create_action("E"),
        ]
    )

    state1_id = graph.add_state(
        state1,
        depth=1
    )

    # =====================================================
    # S2
    #
    # F → explored
    # =====================================================

    state2 = create_state(
        "state-2-hash",
        [
            create_action("F"),
        ]
    )

    state2_id = graph.add_state(
        state2,
        depth=1
    )

    memory.mark_executed(
        state2.state_hash,
        "F"
    )

    return (
        graph,
        memory,
        state0_id,
        state1_id,
        state2_id
    )


def test_partial_state_coverage():
    """
    Verify S0:

        2 explored
        1 unexplored
        66.67% coverage
    """

    (
        graph,
        memory,
        state0_id,
        _,
        _
    ) = create_test_environment()

    engine = CoverageEngine(
        graph,
        memory
    )

    coverage = (
        engine.calculate_state_coverage(
            state0_id
        )
    )

    assert coverage is not None

    assert coverage.total_actions == 3

    assert coverage.explored_actions == 2

    assert coverage.unexplored_actions == 1

    assert (
        coverage.coverage_percentage
        == 66.67
    )

    assert (
        coverage.is_partially_explored
        is True
    )

    print()
    print(
        "PARTIAL STATE COVERAGE TEST PASSED"
    )


def test_unexplored_state_coverage():
    """
    Verify S1:

        0 explored
        2 unexplored
        0% coverage
    """

    (
        graph,
        memory,
        _,
        state1_id,
        _
    ) = create_test_environment()

    engine = CoverageEngine(
        graph,
        memory
    )

    coverage = (
        engine.calculate_state_coverage(
            state1_id
        )
    )

    assert coverage is not None

    assert coverage.total_actions == 2

    assert coverage.explored_actions == 0

    assert coverage.unexplored_actions == 2

    assert coverage.coverage_percentage == 0.0

    assert coverage.is_unexplored is True

    print()
    print(
        "UNEXPLORED STATE COVERAGE TEST PASSED"
    )


def test_fully_explored_state_coverage():
    """
    Verify S2:

        1 explored
        0 unexplored
        100% coverage
    """

    (
        graph,
        memory,
        _,
        _,
        state2_id
    ) = create_test_environment()

    engine = CoverageEngine(
        graph,
        memory
    )

    coverage = (
        engine.calculate_state_coverage(
            state2_id
        )
    )

    assert coverage is not None

    assert coverage.total_actions == 1

    assert coverage.explored_actions == 1

    assert coverage.unexplored_actions == 0

    assert coverage.coverage_percentage == 100.0

    assert coverage.is_fully_explored is True

    print()
    print(
        "FULL STATE COVERAGE TEST PASSED"
    )


def test_global_coverage_report():
    """
    Verify complete graph coverage.

    Expected:

        States:              3
        Actions:             6
        Explored:            3
        Unexplored:          3
        Coverage:            50%

        Fully Explored:      1
        Partially Explored:  1
        Unexplored:          1
    """

    (
        graph,
        memory,
        _,
        _,
        _
    ) = create_test_environment()

    engine = CoverageEngine(
        graph,
        memory
    )

    report = engine.calculate_report()

    assert report.total_states == 3

    assert report.total_actions == 6

    assert report.explored_actions == 3

    assert report.unexplored_actions == 3

    assert (
        report.action_coverage_percentage
        == 50.0
    )

    assert (
        report.fully_explored_states
        == 1
    )

    assert (
        report.partially_explored_states
        == 1
    )

    assert report.unexplored_states == 1

    assert len(
        report.state_coverage
    ) == 3

    print()
    print(
        "GLOBAL COVERAGE REPORT TEST PASSED"
    )


def test_states_with_unexplored_actions():
    """
    Verify that only S0 and S1 are returned.

    S2 is fully explored.
    """

    (
        graph,
        memory,
        state0_id,
        state1_id,
        _
    ) = create_test_environment()

    engine = CoverageEngine(
        graph,
        memory
    )

    states = (
        engine
        .get_states_with_unexplored_actions()
    )

    state_ids = {
        coverage.state_id
        for coverage
        in states
    }

    assert state0_id in state_ids

    assert state1_id in state_ids

    assert len(state_ids) == 2

    print()
    print(
        "UNEXPLORED STATES QUERY TEST PASSED"
    )


def run_all_tests():
    """
    Run all Coverage Engine unit tests.
    """

    test_partial_state_coverage()

    test_unexplored_state_coverage()

    test_fully_explored_state_coverage()

    test_global_coverage_report()

    test_states_with_unexplored_actions()

    print()
    print(
        "======================================"
    )

    print(
        "ALL COVERAGE ENGINE TESTS PASSED"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    run_all_tests()