"""
File:
    test_state_graph_serializer.py

Purpose:
    Verify exact serialization and deserialization of StateGraph.

Round Trip:

    Runtime StateGraph
        ↓
    StateGraphSerializer
        ↓
    JSON-Compatible Dictionary
        ↓
    StateGraphSerializer
        ↓
    Reconstructed Usable StateGraph

What These Tests Prove:

    1. Graph snapshots are JSON-compatible.

    2. Application states survive loading.

    3. StateNode depth and visit metadata survive.

    4. Transitions and nested actions survive.

    5. hash_index is rebuilt correctly.

    6. Graph navigation still works after loading.

    7. Existing hashes still deduplicate after loading.

    8. Shorter paths still update depth after loading.

    9. New states and transitions can still be added.

    10. Invalid serialized graph references are rejected.
"""

import json

from datetime import datetime

from core.graph.state_graph import (
    StateGraph,
)

from core.models.action import (
    Action,
)

from core.models.action_type import (
    ActionType,
)

from core.models.state import (
    ApplicationState,
)

from agent.persistence.state_graph_serializer import (
    StateGraphSerializer,
)

# =============================================================
# TEST FIXTURES
# =============================================================


def create_action(
    action_id: str,
    target: str,
) -> Action:
    """
    Create a deterministic CLICK action.
    """

    return Action(
        action_id=action_id,
        action_type=ActionType.CLICK,
        target=target,
        value=None,
        timestamp=datetime(
            2026,
            7,
            5,
            10,
            0,
            0,
        ),
        description=(f"Click {target}"),
    )


def create_state(
    state_id: str,
    state_hash: str,
    available_actions=None,
) -> ApplicationState:
    """
    Create a deterministic ApplicationState.
    """

    return ApplicationState(
        state_id=state_id,
        timestamp=datetime(
            2026,
            7,
            5,
            11,
            0,
            0,
        ),
        window_title="Test Application",
        controls=[],
        values={
            "state": state_id,
        },
        available_actions=(available_actions or []),
        screenshot_path=(f"screenshots/{state_id}.png"),
        metadata={
            "fixture": True,
        },
        state_hash=state_hash,
    )


def create_test_graph() -> StateGraph:
    """
    Create the controlled graph:

        S0
         |
         | CLICK(buttonA)
         v
        S1
         |
         | CLICK(buttonB)
         v
        S2

    Metadata:

        S0:
            depth = 0
            visits = 1

        S1:
            depth = 1
            visits = 3

        S2:
            depth = 2
            visits = 2
    """

    action_a = create_action(
        action_id="action-A",
        target="buttonA",
    )

    action_b = create_action(
        action_id="action-B",
        target="buttonB",
    )

    state_0 = create_state(
        state_id="S0",
        state_hash="hash-S0",
        available_actions=[
            action_a,
        ],
    )

    state_1 = create_state(
        state_id="S1",
        state_hash="hash-S1",
        available_actions=[
            action_b,
        ],
    )

    state_2 = create_state(
        state_id="S2",
        state_hash="hash-S2",
    )

    graph = StateGraph()

    graph.add_state(
        state_0,
        depth=0,
    )

    graph.add_state(
        state_1,
        depth=1,
    )

    graph.add_state(
        state_2,
        depth=2,
    )

    # Restore the exact controlled visit metadata.
    #
    # We set it explicitly because this fixture is testing
    # persistence, not add_state() visit behavior.
    graph.get_state("S1").visits = 3

    graph.get_state("S2").visits = 2

    graph.add_transition(
        source_id="S0",
        action=action_a,
        target_id="S1",
        success=True,
        duration=1.25,
    )

    graph.add_transition(
        source_id="S1",
        action=action_b,
        target_id="S2",
        success=True,
        duration=1.75,
    )

    return graph


def round_trip_graph():
    """
    Create, serialize, and deserialize the controlled graph.
    """

    original = create_test_graph()

    serialized = StateGraphSerializer.serialize(original)

    restored = StateGraphSerializer.deserialize(serialized)

    return (
        original,
        serialized,
        restored,
    )


def get_transition_count(
    graph: StateGraph,
) -> int:
    """
    Return total transitions stored in the graph.
    """

    return sum(len(transitions) for transitions in graph.edges.values())


# =============================================================
# SERIALIZATION TESTS
# =============================================================


def test_graph_serialization_is_json_compatible():
    """
    Complete graph data must be directly accepted by json.dumps.
    """

    graph = create_test_graph()

    serialized = StateGraphSerializer.serialize(graph)

    json_text = json.dumps(serialized)

    assert json_text is not None

    assert len(serialized["states"]) == 3

    assert len(serialized["transitions"]) == 2


def test_graph_serialization_is_deterministic():
    """
    State records must be serialized in state-ID order.
    """

    graph = create_test_graph()

    serialized = StateGraphSerializer.serialize(graph)

    serialized_state_ids = [
        state_record["state_id"] for state_record in serialized["states"]
    ]

    assert serialized_state_ids == [
        "S0",
        "S1",
        "S2",
    ]


# =============================================================
# STATE ROUND-TRIP TESTS
# =============================================================


def test_graph_round_trip_preserves_all_states():
    """
    Every state must survive loading.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert len(restored.states) == 3

    assert restored.get_state("S0") is not None

    assert restored.get_state("S1") is not None

    assert restored.get_state("S2") is not None


def test_graph_round_trip_preserves_state_data():
    """
    ApplicationState data must survive inside each StateNode.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_graph()

    original_state = original.get_state("S1").state

    restored_state = restored.get_state("S1").state

    assert restored_state.state_id == original_state.state_id

    assert restored_state.state_hash == original_state.state_hash

    assert restored_state.timestamp == original_state.timestamp

    assert restored_state.values == original_state.values

    assert restored_state.screenshot_path == original_state.screenshot_path

    assert len(restored_state.available_actions) == 1

    assert isinstance(
        restored_state.available_actions[0],
        Action,
    )


def test_graph_round_trip_preserves_depths():
    """
    Shortest-known graph depths must survive.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert restored.get_state_depth("S0") == 0

    assert restored.get_state_depth("S1") == 1

    assert restored.get_state_depth("S2") == 2


def test_graph_round_trip_preserves_visits():
    """
    StateNode encounter counts must survive.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert restored.get_state("S0").visits == 1

    assert restored.get_state("S1").visits == 3

    assert restored.get_state("S2").visits == 2


# =============================================================
# INDEX RECONSTRUCTION TESTS
# =============================================================


def test_hash_index_is_rebuilt():
    """
    Loaded graph must rebuild hash → state-ID lookup.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert restored.hash_index["hash-S0"] == "S0"

    assert restored.hash_index["hash-S1"] == "S1"

    assert restored.hash_index["hash-S2"] == "S2"


def test_has_state_works_after_loading():
    """
    Hash-based state existence checks must remain functional.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert restored.has_state("hash-S1")

    assert not restored.has_state("missing-hash")


# =============================================================
# TRANSITION ROUND-TRIP TESTS
# =============================================================


def test_graph_round_trip_preserves_transitions():
    """
    Every transition must survive loading.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert get_transition_count(restored) == 2

    transition_0 = restored.edges["S0"][0]

    transition_1 = restored.edges["S1"][0]

    assert transition_0.source_state == "S0"

    assert transition_0.target_state == "S1"

    assert transition_1.source_state == "S1"

    assert transition_1.target_state == "S2"


def test_transition_actions_are_reconstructed():
    """
    Loaded transitions must contain real Action objects.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    transition = restored.edges["S0"][0]

    assert isinstance(
        transition.action,
        Action,
    )

    assert transition.action.action_id == "action-A"

    assert transition.action.action_type == ActionType.CLICK

    assert transition.action.target == "buttonA"

    assert transition.duration == 1.25


# =============================================================
# GRAPH NAVIGATION TESTS
# =============================================================


def test_get_neighbors_works_after_loading():
    """
    Neighbor lookup must use restored transitions correctly.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    assert restored.get_neighbors("S0") == ["S1"]

    assert restored.get_neighbors("S1") == ["S2"]


def test_find_path_works_after_loading():
    """
    GraphSearch must work against the reconstructed graph.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    path = restored.find_path(
        "S0",
        "S2",
    )

    assert path == [
        "S0",
        "S1",
        "S2",
    ]


def test_find_transition_path_works_after_loading():
    """
    Replay-oriented transition path search must remain usable.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    path = restored.find_transition_path(
        "S0",
        "S2",
    )

    assert path is not None

    assert len(path) == 2

    assert path[0].action.target == "buttonA"

    assert path[1].action.target == "buttonB"


# =============================================================
# POST-LOAD RUNTIME BEHAVIOR TESTS
# =============================================================


def test_existing_hash_deduplicates_after_loading():
    """
    Adding an already-known state hash must return the existing ID
    and increment visits rather than create a duplicate.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    existing_node = restored.get_state("S1")

    visits_before = existing_node.visits

    duplicate_state = create_state(
        state_id="DIFFERENT-ID",
        state_hash="hash-S1",
    )

    returned_state_id = restored.add_state(
        duplicate_state,
        depth=5,
    )

    assert returned_state_id == "S1"

    assert len(restored.states) == 3

    assert restored.get_state("S1").visits == visits_before + 1


def test_shorter_depth_updates_after_loading():
    """
    Existing-state depth optimization must still work.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    duplicate_state = create_state(
        state_id="DIFFERENT-ID",
        state_hash="hash-S2",
    )

    restored.add_state(
        duplicate_state,
        depth=1,
    )

    assert restored.get_state_depth("S2") == 1


def test_new_state_can_be_added_after_loading():
    """
    Loaded graph must accept new exploration discoveries.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    state_3 = create_state(
        state_id="S3",
        state_hash="hash-S3",
    )

    returned_state_id = restored.add_state(
        state_3,
        depth=3,
    )

    assert returned_state_id == "S3"

    assert restored.get_state("S3") is not None

    assert restored.has_state("hash-S3")

    assert restored.get_state_depth("S3") == 3

    assert restored.edges["S3"] == []


def test_new_transition_can_be_added_after_loading():
    """
    Loaded graph must continue accepting transitions.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_graph()

    state_3 = create_state(
        state_id="S3",
        state_hash="hash-S3",
    )

    restored.add_state(
        state_3,
        depth=3,
    )

    action_c = create_action(
        action_id="action-C",
        target="buttonC",
    )

    transition = restored.add_transition(
        source_id="S2",
        action=action_c,
        target_id="S3",
        success=True,
        duration=2.0,
    )

    assert get_transition_count(restored) == 3

    assert transition.source_state == "S2"

    assert transition.target_state == "S3"

    assert restored.get_neighbors("S2") == ["S3"]


# =============================================================
# INVALID SNAPSHOT TESTS
# =============================================================


def test_state_id_mismatch_is_rejected():
    """
    Wrapper state ID and ApplicationState.state_id must agree.
    """

    graph = create_test_graph()

    serialized = StateGraphSerializer.serialize(graph)

    serialized["states"][0]["state_id"] = "WRONG-ID"

    try:

        StateGraphSerializer.deserialize(serialized)

        assert False, "Expected state ID mismatch " "to raise ValueError."

    except ValueError as error:

        assert "state ID" in str(error)


def test_missing_transition_source_is_rejected():
    """
    Transition source references must point to loaded states.
    """

    graph = create_test_graph()

    serialized = StateGraphSerializer.serialize(graph)

    serialized["transitions"][0]["source_state"] = "MISSING-SOURCE"

    try:

        StateGraphSerializer.deserialize(serialized)

        assert False, "Expected missing source " "to raise ValueError."

    except ValueError as error:

        assert "source state" in str(error)


def test_missing_transition_target_is_rejected():
    """
    Transition target references must point to loaded states.
    """

    graph = create_test_graph()

    serialized = StateGraphSerializer.serialize(graph)

    serialized["transitions"][0]["target_state"] = "MISSING-TARGET"

    try:

        StateGraphSerializer.deserialize(serialized)

        assert False, "Expected missing target " "to raise ValueError."

    except ValueError as error:

        assert "target state" in str(error)


# =============================================================
# COMPLETE TEST RUNNER
# =============================================================


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_graph_serialization_is_json_compatible,
        test_graph_serialization_is_deterministic,
        test_graph_round_trip_preserves_all_states,
        test_graph_round_trip_preserves_state_data,
        test_graph_round_trip_preserves_depths,
        test_graph_round_trip_preserves_visits,
        test_hash_index_is_rebuilt,
        test_has_state_works_after_loading,
        test_graph_round_trip_preserves_transitions,
        test_transition_actions_are_reconstructed,
        test_get_neighbors_works_after_loading,
        test_find_path_works_after_loading,
        test_find_transition_path_works_after_loading,
        test_existing_hash_deduplicates_after_loading,
        test_shorter_depth_updates_after_loading,
        test_new_state_can_be_added_after_loading,
        test_new_transition_can_be_added_after_loading,
        test_state_id_mismatch_is_rejected,
        test_missing_transition_source_is_rejected,
        test_missing_transition_target_is_rejected,
    ]

    print()

    print("===== STATE GRAPH SERIALIZER TESTS =====")

    print()

    for test in tests:

        test()

        print(f"PASS: {test.__name__}")

    print()

    print("All StateGraphSerializer tests passed successfully.")


if __name__ == "__main__":

    main()
