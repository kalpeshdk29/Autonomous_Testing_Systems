"""
File: test_state_depth.py

Purpose:
    Verify StateGraph depth tracking.

Tests:
    1. Root depth.
    2. Child depth.
    3. Duplicate state depth preservation.
    4. Shorter path depth update.
    5. Longer path rejection.

Important:
    These are pure unit tests.

    No real application is launched.
"""

from core.graph.state_graph import (
    StateGraph
)

from core.models.state import (
    ApplicationState
)


def create_test_state(
    state_hash: str
) -> ApplicationState:
    """
    Create a minimal ApplicationState for graph testing.

    Parameters
    ----------
    state_hash:
        Deterministic hash used for deduplication.

    Returns
    -------
    ApplicationState:
        Minimal test state.
    """

    return ApplicationState(
        window_title="Test Application",
        state_hash=state_hash
    )


def test_root_depth():
    """
    Verify that the root state can be stored
    at depth zero.
    """

    graph = StateGraph()

    root = create_test_state(
        "root-hash"
    )

    root_id = graph.add_state(
        root,
        depth=0
    )

    assert (
        graph.get_state_depth(
            root_id
        )
        == 0
    )

    print()
    print(
        "ROOT DEPTH TEST PASSED"
    )


def test_child_depth():
    """
    Verify that a child state can be stored
    at depth one.
    """

    graph = StateGraph()

    child = create_test_state(
        "child-hash"
    )

    child_id = graph.add_state(
        child,
        depth=1
    )

    assert (
        graph.get_state_depth(
            child_id
        )
        == 1
    )

    print()
    print(
        "CHILD DEPTH TEST PASSED"
    )


def test_duplicate_preserves_shortest_depth():
    """
    Verify that rediscovering a state through
    a longer path does not increase its depth.

    First discovery:

        depth = 1

    Later discovery:

        depth = 5

    Expected:

        depth remains 1
    """

    graph = StateGraph()

    state1 = create_test_state(
        "same-hash"
    )

    state_id = graph.add_state(
        state1,
        depth=1
    )

    duplicate = create_test_state(
        "same-hash"
    )

    duplicate_id = graph.add_state(
        duplicate,
        depth=5
    )

    assert state_id == duplicate_id

    assert (
        graph.get_state_depth(
            state_id
        )
        == 1
    )

    print()
    print(
        "LONGER DEPTH REJECTION TEST PASSED"
    )


def test_shorter_path_updates_depth():
    """
    Verify that discovering a shorter path
    updates the stored state depth.

    First discovery:

        S0 → S1 → S2 → S3

        depth = 3

    Later discovery:

        S0 → S3

        depth = 1

    Expected:

        S3 depth becomes 1
    """

    graph = StateGraph()

    state1 = create_test_state(
        "target-hash"
    )

    state_id = graph.add_state(
        state1,
        depth=3
    )

    assert (
        graph.get_state_depth(
            state_id
        )
        == 3
    )

    duplicate = create_test_state(
        "target-hash"
    )

    duplicate_id = graph.add_state(
        duplicate,
        depth=1
    )

    assert state_id == duplicate_id

    assert (
        graph.get_state_depth(
            state_id
        )
        == 1
    )

    print()
    print(
        "SHORTER PATH DEPTH UPDATE TEST PASSED"
    )


def test_manual_depth_update():
    """
    Verify direct graph depth updates.
    """

    graph = StateGraph()

    state = create_test_state(
        "manual-update-hash"
    )

    state_id = graph.add_state(
        state,
        depth=4
    )

    updated = graph.update_state_depth(
        state_id,
        depth=2
    )

    assert updated is True

    assert (
        graph.get_state_depth(
            state_id
        )
        == 2
    )

    #
    # Attempt a worse depth.
    #
    updated = graph.update_state_depth(
        state_id,
        depth=6
    )

    assert updated is False

    assert (
        graph.get_state_depth(
            state_id
        )
        == 2
    )

    print()
    print(
        "MANUAL DEPTH UPDATE TEST PASSED"
    )


def run_all_tests():
    """
    Run every state-depth unit test.
    """

    test_root_depth()

    test_child_depth()

    test_duplicate_preserves_shortest_depth()

    test_shorter_path_updates_depth()

    test_manual_depth_update()

    print()
    print(
        "======================================"
    )

    print(
        "ALL STATE DEPTH TESTS PASSED"
    )

    print(
        "======================================"
    )


if __name__ == "__main__":

    run_all_tests()