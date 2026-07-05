"""
File:
    test_session_serializer.py

Purpose:
    Verify serialization and deserialization of a complete
    versioned exploration session.

Round Trip:

    ExplorationSessionSnapshot
            ↓
    SessionSerializer
            ↓
    JSON-Compatible Dictionary
            ↓
    SessionSerializer
            ↓
    Reconstructed ExplorationSessionSnapshot

What These Tests Prove:

    1. Complete session snapshots are JSON-compatible.

    2. Schema version survives.

    3. Session identity survives.

    4. Root-state identity survives.

    5. Session timestamps survive exactly.

    6. StateGraph survives as a usable runtime graph.

    7. ExplorationMemory survives as usable runtime memory.

    8. Coverage before and after persistence is identical.

    9. Loaded graph and memory remain mutable.

    10. Unsupported schema versions are rejected.

    11. Missing session metadata is rejected.

    12. Missing required session fields are rejected.

    13. A root state absent from the graph is rejected.
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

from agent.coverage.coverage_engine import (
    CoverageEngine,
)

from agent.explorer.action_filter import (
    ActionFilter,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.persistence.session_serializer import (
    SessionSerializer,
)

from agent.persistence.session_snapshot import (
    ExplorationSessionSnapshot,
)

# =============================================================
# CONTROLLED ACTION FILTER
# =============================================================


class SessionTestActionFilter(ActionFilter):
    """
    Controlled action policy for session persistence tests.

    Only these actions are eligible:

        buttonA
        buttonB
        buttonC
    """

    ALLOWED_TARGETS = {
        "buttonA",
        "buttonB",
        "buttonC",
    }

    def allow(
        self,
        action,
    ) -> bool:
        """
        Return True only for controlled test actions.
        """

        return action.target in self.ALLOWED_TARGETS


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

    Available eligible actions:

        S0:
            buttonA
            buttonB

        S1:
            buttonC

    Exploration history will later mark:

        S0 / buttonA = executed

    Expected eligible coverage:

        total eligible      = 3
        explored eligible   = 1
        unexplored eligible = 2
    """

    action_a = create_action(
        action_id="action-A",
        target="buttonA",
    )

    action_b = create_action(
        action_id="action-B",
        target="buttonB",
    )

    action_c = create_action(
        action_id="action-C",
        target="buttonC",
    )

    state_0 = create_state(
        state_id="S0",
        state_hash="hash-S0",
        available_actions=[
            action_a,
            action_b,
        ],
    )

    state_1 = create_state(
        state_id="S1",
        state_hash="hash-S1",
        available_actions=[
            action_c,
        ],
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

    graph.add_transition(
        source_id="S0",
        action=action_a,
        target_id="S1",
        success=True,
        duration=1.25,
    )

    return graph


def create_test_memory() -> ExplorationMemory:
    """
    Create deterministic exploration history.
    """

    memory = ExplorationMemory()

    memory.mark_executed(
        "hash-S0",
        "buttonA",
    )

    return memory


def create_test_snapshot() -> ExplorationSessionSnapshot:
    """
    Create a complete deterministic session snapshot.
    """

    return ExplorationSessionSnapshot(
        schema_version=(SessionSerializer.CURRENT_SCHEMA_VERSION),
        session_id="session-123",
        root_state_id="S0",
        created_at=datetime(
            2026,
            7,
            5,
            9,
            0,
            0,
        ),
        updated_at=datetime(
            2026,
            7,
            5,
            12,
            30,
            45,
        ),
        graph=create_test_graph(),
        memory=create_test_memory(),
    )


def round_trip_snapshot():
    """
    Create, serialize, and deserialize a complete session.
    """

    original = create_test_snapshot()

    serialized = SessionSerializer.serialize(original)

    restored = SessionSerializer.deserialize(serialized)

    return (
        original,
        serialized,
        restored,
    )


def get_transition_count(
    graph: StateGraph,
) -> int:
    """
    Return total transitions stored in StateGraph.
    """

    return sum(len(transitions) for transitions in graph.edges.values())


def get_coverage_values(
    graph,
    memory,
) -> dict:
    """
    Calculate stable aggregate coverage values.

    The same ActionFilter is used before and after persistence.
    """

    coverage_engine = CoverageEngine(
        graph=graph,
        memory=memory,
        action_filter=(SessionTestActionFilter()),
    )

    report = coverage_engine.calculate_report()

    return {
        "total_states": (report.total_states),
        "eligible_total_actions": (report.eligible_total_actions),
        "eligible_explored_actions": (report.eligible_explored_actions),
        "eligible_unexplored_actions": (report.eligible_unexplored_actions),
        "eligible_action_coverage_percentage": (
            report.eligible_action_coverage_percentage
        ),
    }


# =============================================================
# SERIALIZATION TESTS
# =============================================================


def test_session_serialization_is_json_compatible():
    """
    Complete session data must be accepted directly by json.dumps.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    json_text = json.dumps(serialized)

    assert json_text is not None

    assert serialized["schema_version"] == SessionSerializer.CURRENT_SCHEMA_VERSION

    assert "session" in serialized

    assert "graph" in serialized

    assert "memory" in serialized


def test_serialized_session_has_expected_structure():
    """
    Verify the top-level versioned session format.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    assert set(serialized.keys()) == {
        "schema_version",
        "session",
        "graph",
        "memory",
    }

    assert serialized["session"]["session_id"] == "session-123"

    assert serialized["session"]["root_state_id"] == "S0"


# =============================================================
# METADATA ROUND-TRIP TESTS
# =============================================================


def test_session_round_trip_preserves_schema_version():
    """
    Persistence schema identity must survive.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_snapshot()

    assert restored.schema_version == original.schema_version


def test_session_round_trip_preserves_session_id():
    """
    Stable session identity must survive.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_snapshot()

    assert restored.session_id == original.session_id


def test_session_round_trip_preserves_root_state_id():
    """
    Replay root identity must survive.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_snapshot()

    assert restored.root_state_id == original.root_state_id

    assert restored.graph.get_state(restored.root_state_id) is not None


def test_session_round_trip_preserves_timestamps():
    """
    Session creation and update times must survive exactly.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_snapshot()

    assert restored.created_at == original.created_at

    assert restored.updated_at == original.updated_at


# =============================================================
# GRAPH ROUND-TRIP TESTS
# =============================================================


def test_session_round_trip_preserves_graph():
    """
    Complete graph structure must survive inside the session.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_snapshot()

    assert len(restored.graph.states) == len(original.graph.states)

    assert get_transition_count(restored.graph) == get_transition_count(original.graph)

    assert restored.graph.get_state_depth("S0") == 0

    assert restored.graph.get_state_depth("S1") == 1

    assert restored.graph.find_path(
        "S0",
        "S1",
    ) == [
        "S0",
        "S1",
    ]


# =============================================================
# MEMORY ROUND-TRIP TESTS
# =============================================================


def test_session_round_trip_preserves_memory():
    """
    Exploration history must survive inside the session.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_snapshot()

    assert restored.memory.is_executed(
        "hash-S0",
        "buttonA",
    )

    assert not restored.memory.is_executed(
        "hash-S0",
        "buttonB",
    )

    assert not restored.memory.is_executed(
        "hash-S1",
        "buttonC",
    )


# =============================================================
# COVERAGE EQUIVALENCE TEST
# =============================================================


def test_coverage_is_identical_after_round_trip():
    """
    This is the strongest session persistence invariant.

    The same:

        Graph
        Memory
        ActionFilter

    must produce exactly the same CoverageReport values before
    and after persistence.
    """

    (
        original,
        _,
        restored,
    ) = round_trip_snapshot()

    coverage_before = get_coverage_values(
        graph=original.graph,
        memory=original.memory,
    )

    coverage_after = get_coverage_values(
        graph=restored.graph,
        memory=restored.memory,
    )

    assert coverage_after == coverage_before

    assert coverage_after["total_states"] == 2

    assert coverage_after["eligible_total_actions"] == 3

    assert coverage_after["eligible_explored_actions"] == 1

    assert coverage_after["eligible_unexplored_actions"] == 2


# =============================================================
# POST-LOAD RUNTIME BEHAVIOR TESTS
# =============================================================


def test_loaded_graph_remains_mutable():
    """
    A restored session graph must continue accepting discoveries.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_snapshot()

    action_d = create_action(
        action_id="action-D",
        target="buttonD",
    )

    state_2 = create_state(
        state_id="S2",
        state_hash="hash-S2",
        available_actions=[
            action_d,
        ],
    )

    restored.graph.add_state(
        state_2,
        depth=2,
    )

    restored.graph.add_transition(
        source_id="S1",
        action=action_d,
        target_id="S2",
        success=True,
        duration=2.0,
    )

    assert restored.graph.get_state("S2") is not None

    assert restored.graph.find_path(
        "S0",
        "S2",
    ) == [
        "S0",
        "S1",
        "S2",
    ]


def test_loaded_memory_remains_mutable():
    """
    A restored session memory must continue recording exploration.
    """

    (
        _,
        _,
        restored,
    ) = round_trip_snapshot()

    restored.memory.mark_executed(
        "hash-S1",
        "buttonC",
    )

    assert restored.memory.is_executed(
        "hash-S1",
        "buttonC",
    )


# =============================================================
# INVALID SCHEMA TESTS
# =============================================================


def test_unsupported_schema_version_is_rejected():
    """
    Unknown persistence formats must not be loaded silently.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    serialized["schema_version"] = 999

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected unsupported schema version " "to raise ValueError."

    except ValueError as error:

        assert "Unsupported session schema version" in str(error)


def test_snapshot_with_unsupported_schema_is_rejected():
    """
    Serialization must also reject unsupported runtime snapshots.
    """

    snapshot = create_test_snapshot()

    snapshot.schema_version = 999

    try:

        SessionSerializer.serialize(snapshot)

        assert False, "Expected unsupported snapshot schema " "to raise ValueError."

    except ValueError as error:

        assert "Unsupported session schema version" in str(error)


# =============================================================
# INVALID METADATA TESTS
# =============================================================


def test_missing_session_metadata_is_rejected():
    """
    Session metadata is required.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    del serialized["session"]

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected missing session metadata " "to raise ValueError."

    except ValueError as error:

        assert "session metadata" in str(error)


def test_missing_session_id_is_rejected():
    """
    Stable session identity is required.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    serialized["session"]["session_id"] = None

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected missing session_id " "to raise ValueError."

    except ValueError as error:

        assert "session_id" in str(error)


def test_missing_root_state_id_is_rejected():
    """
    Replay root identity is required.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    serialized["session"]["root_state_id"] = None

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected missing root_state_id " "to raise ValueError."

    except ValueError as error:

        assert "root_state_id" in str(error)


def test_missing_created_at_is_rejected():
    """
    Session creation timestamp is required.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    serialized["session"]["created_at"] = None

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected missing created_at " "to raise ValueError."

    except ValueError as error:

        assert "created_at" in str(error)


def test_missing_updated_at_is_rejected():
    """
    Session update timestamp is required.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    serialized["session"]["updated_at"] = None

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected missing updated_at " "to raise ValueError."

    except ValueError as error:

        assert "updated_at" in str(error)


# =============================================================
# ROOT-STATE INTEGRITY TESTS
# =============================================================


def test_serialization_rejects_root_missing_from_graph():
    """
    A runtime snapshot is not resumable if its root does not exist.
    """

    snapshot = create_test_snapshot()

    snapshot.root_state_id = "MISSING-ROOT"

    try:

        SessionSerializer.serialize(snapshot)

        assert False, "Expected missing runtime root state " "to raise ValueError."

    except ValueError as error:

        assert "root state" in str(error)


def test_deserialization_rejects_root_missing_from_graph():
    """
    Serialized root references must point to a real loaded state.
    """

    snapshot = create_test_snapshot()

    serialized = SessionSerializer.serialize(snapshot)

    serialized["session"]["root_state_id"] = "MISSING-ROOT"

    try:

        SessionSerializer.deserialize(serialized)

        assert False, "Expected missing serialized root state " "to raise ValueError."

    except ValueError as error:

        assert "root state" in str(error)


# =============================================================
# COMPLETE TEST RUNNER
# =============================================================


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_session_serialization_is_json_compatible,
        test_serialized_session_has_expected_structure,
        test_session_round_trip_preserves_schema_version,
        test_session_round_trip_preserves_session_id,
        test_session_round_trip_preserves_root_state_id,
        test_session_round_trip_preserves_timestamps,
        test_session_round_trip_preserves_graph,
        test_session_round_trip_preserves_memory,
        test_coverage_is_identical_after_round_trip,
        test_loaded_graph_remains_mutable,
        test_loaded_memory_remains_mutable,
        test_unsupported_schema_version_is_rejected,
        test_snapshot_with_unsupported_schema_is_rejected,
        test_missing_session_metadata_is_rejected,
        test_missing_session_id_is_rejected,
        test_missing_root_state_id_is_rejected,
        test_missing_created_at_is_rejected,
        test_missing_updated_at_is_rejected,
        test_serialization_rejects_root_missing_from_graph,
        test_deserialization_rejects_root_missing_from_graph,
    ]

    print()

    print("===== SESSION SERIALIZER TESTS =====")

    print()

    for test in tests:

        test()

        print(f"PASS: {test.__name__}")

    print()

    print("All SessionSerializer tests passed successfully.")


if __name__ == "__main__":

    main()
