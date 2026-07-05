"""
File:
    test_domain_serializer.py

Purpose:
    Verify exact serialization and deserialization of the core
    exploration domain objects.

Round Trip:

    Runtime Object
        ↓
    DomainSerializer
        ↓
    JSON-Compatible Dictionary
        ↓
    DomainSerializer
        ↓
    Reconstructed Runtime Object

What These Tests Prove:

    1. Action identity and metadata survive serialization.

    2. ActionType enum values are restored correctly.

    3. ApplicationState identity, timestamps, hashes, values,
       metadata, screenshot paths, and available actions survive.

    4. Transition references and execution metadata survive.

    5. Transition actions are reconstructed as real Action objects.

    6. ExplorationMemory survives conversion from:

           defaultdict(set)

       to:

           dict[list]

       and back.

    7. Serialized output is JSON-compatible.
"""

import json

from datetime import datetime

from core.models.action import (
    Action,
)

from core.models.action_type import (
    ActionType,
)

from core.models.state import (
    ApplicationState,
)

from core.models.transition import (
    Transition,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.persistence.domain_serializer import (
    DomainSerializer,
)


# =============================================================
# TEST FIXTURES
# =============================================================


def create_test_action() -> Action:
    """
    Create a deterministic Action.

    Explicit values are used for generated fields so the test can
    prove that persistence restores them instead of creating new
    IDs or timestamps.
    """

    return Action(
        action_id="action-123",
        action_type=ActionType.TEXT_INPUT,
        target="searchBox",
        value="calculator",
        timestamp=datetime(
            2026,
            7,
            5,
            10,
            30,
            45,
        ),
        description="Enter calculator search text",
    )


def create_test_state() -> ApplicationState:
    """
    Create a deterministic ApplicationState.

    Controls are intentionally empty in this first serializer test.

    Nested UIControl persistence will already be exercised naturally
    when we save a real captured Calculator state later.

    This unit test focuses on the ApplicationState fields and nested
    Action reconstruction.
    """

    action = create_test_action()

    return ApplicationState(
        state_id="state-123",
        timestamp=datetime(
            2026,
            7,
            5,
            11,
            15,
            30,
        ),
        window_title="Calculator",
        controls=[],
        values={
            "display": "78",
            "expression": "7 + 8",
        },
        available_actions=[
            action,
        ],
        screenshot_path=(
            "screenshots/state-123.png"
        ),
        metadata={
            "capture_source": "unit_test",
            "stable": True,
            "attempt": 3,
        },
        state_hash="hash-state-123",
    )


# =============================================================
# ACTION TESTS
# =============================================================


def test_action_serialization_is_json_compatible():
    """
    Serialized Action data must be directly accepted by json.dumps.

    This proves:

        ActionType → string
        datetime   → ISO string
    """

    action = create_test_action()

    serialized = (
        DomainSerializer.serialize_action(
            action
        )
    )

    json_text = json.dumps(
        serialized
    )

    assert json_text is not None

    assert (
        serialized["action_id"]
        ==
        "action-123"
    )

    assert (
        serialized["action_type"]
        ==
        "TEXT_INPUT"
    )

    assert (
        serialized["timestamp"]
        ==
        "2026-07-05T10:30:45"
    )


def test_action_round_trip_preserves_all_fields():
    """
    Action serialization and deserialization must preserve every
    persisted field exactly.
    """

    original = create_test_action()

    serialized = (
        DomainSerializer.serialize_action(
            original
        )
    )

    restored = (
        DomainSerializer.deserialize_action(
            serialized
        )
    )

    assert isinstance(
        restored,
        Action,
    )

    assert (
        restored.action_id
        ==
        original.action_id
    )

    assert (
        restored.action_type
        ==
        original.action_type
    )

    assert isinstance(
        restored.action_type,
        ActionType,
    )

    assert (
        restored.target
        ==
        original.target
    )

    assert (
        restored.value
        ==
        original.value
    )

    assert (
        restored.timestamp
        ==
        original.timestamp
    )

    assert (
        restored.description
        ==
        original.description
    )


# =============================================================
# APPLICATION STATE TESTS
# =============================================================


def test_state_serialization_is_json_compatible():
    """
    Serialized ApplicationState data must be directly JSON-compatible.
    """

    state = create_test_state()

    serialized = (
        DomainSerializer.serialize_state(
            state
        )
    )

    json_text = json.dumps(
        serialized
    )

    assert json_text is not None

    assert (
        serialized["state_id"]
        ==
        "state-123"
    )

    assert (
        serialized["state_hash"]
        ==
        "hash-state-123"
    )

    assert (
        serialized["timestamp"]
        ==
        "2026-07-05T11:15:30"
    )


def test_state_round_trip_preserves_identity_and_observation():
    """
    State identity and observed application values must survive
    serialization.
    """

    original = create_test_state()

    serialized = (
        DomainSerializer.serialize_state(
            original
        )
    )

    restored = (
        DomainSerializer.deserialize_state(
            serialized
        )
    )

    assert isinstance(
        restored,
        ApplicationState,
    )

    assert (
        restored.state_id
        ==
        original.state_id
    )

    assert (
        restored.timestamp
        ==
        original.timestamp
    )

    assert (
        restored.window_title
        ==
        original.window_title
    )

    assert (
        restored.values
        ==
        original.values
    )

    assert (
        restored.screenshot_path
        ==
        original.screenshot_path
    )

    assert (
        restored.metadata
        ==
        original.metadata
    )

    assert (
        restored.state_hash
        ==
        original.state_hash
    )


def test_state_round_trip_reconstructs_nested_actions():
    """
    Available actions must be reconstructed as real Action objects,
    not left as dictionaries.
    """

    original = create_test_state()

    serialized = (
        DomainSerializer.serialize_state(
            original
        )
    )

    restored = (
        DomainSerializer.deserialize_state(
            serialized
        )
    )

    assert (
        len(
            restored.available_actions
        )
        ==
        1
    )

    restored_action = (
        restored.available_actions[0]
    )

    original_action = (
        original.available_actions[0]
    )

    assert isinstance(
        restored_action,
        Action,
    )

    assert isinstance(
        restored_action.action_type,
        ActionType,
    )

    assert (
        restored_action.action_id
        ==
        original_action.action_id
    )

    assert (
        restored_action.action_type
        ==
        original_action.action_type
    )

    assert (
        restored_action.timestamp
        ==
        original_action.timestamp
    )


# =============================================================
# TRANSITION TESTS
# =============================================================


def test_transition_serialization_is_json_compatible():
    """
    Transition serialization must also serialize its nested Action.
    """

    action = create_test_action()

    transition = Transition(
        source_state="state-A",
        target_state="state-B",
        action=action,
        success=True,
        duration=1.75,
    )

    serialized = (
        DomainSerializer.serialize_transition(
            transition
        )
    )

    json_text = json.dumps(
        serialized
    )

    assert json_text is not None

    assert (
        serialized["source_state"]
        ==
        "state-A"
    )

    assert (
        serialized["target_state"]
        ==
        "state-B"
    )

    assert (
        serialized["action"]["action_type"]
        ==
        "TEXT_INPUT"
    )


def test_transition_round_trip_preserves_all_fields():
    """
    Transition references, execution metadata, and nested Action must
    survive the round trip.
    """

    original_action = create_test_action()

    original = Transition(
        source_state="state-A",
        target_state="state-B",
        action=original_action,
        success=False,
        duration=2.5,
    )

    serialized = (
        DomainSerializer.serialize_transition(
            original
        )
    )

    restored = (
        DomainSerializer.deserialize_transition(
            serialized
        )
    )

    assert isinstance(
        restored,
        Transition,
    )

    assert (
        restored.source_state
        ==
        original.source_state
    )

    assert (
        restored.target_state
        ==
        original.target_state
    )

    assert (
        restored.success
        ==
        original.success
    )

    assert (
        restored.duration
        ==
        original.duration
    )

    assert isinstance(
        restored.action,
        Action,
    )

    assert (
        restored.action.action_id
        ==
        original.action.action_id
    )

    assert (
        restored.action.action_type
        ==
        original.action.action_type
    )

    assert (
        restored.action.timestamp
        ==
        original.action.timestamp
    )


# =============================================================
# EXPLORATION MEMORY TESTS
# =============================================================


def create_test_memory() -> ExplorationMemory:
    """
    Create deterministic exploration history.
    """

    memory = ExplorationMemory()

    memory.mark_executed(
        "hash-A",
        "num7Button",
    )

    memory.mark_executed(
        "hash-A",
        "plusButton",
    )

    memory.mark_executed(
        "hash-B",
        "equalButton",
    )

    return memory


def test_memory_serialization_is_json_compatible():
    """
    defaultdict(set) must become normal JSON-compatible structures.
    """

    memory = create_test_memory()

    serialized = (
        DomainSerializer.serialize_memory(
            memory
        )
    )

    json_text = json.dumps(
        serialized
    )

    assert json_text is not None

    assert isinstance(
        serialized["visited_actions"],
        dict,
    )

    assert isinstance(
        serialized[
            "visited_actions"
        ]["hash-A"],
        list,
    )


def test_memory_serialization_is_deterministic():
    """
    Action targets must be sorted in serialized output.

    Deterministic persistence makes snapshots easier to:

        inspect
        compare
        diff
        test
    """

    memory = create_test_memory()

    serialized = (
        DomainSerializer.serialize_memory(
            memory
        )
    )

    assert (
        serialized[
            "visited_actions"
        ]["hash-A"]
        ==
        [
            "num7Button",
            "plusButton",
        ]
    )


def test_memory_round_trip_preserves_exploration_history():
    """
    Every state hash and executed action target must survive loading.
    """

    original = create_test_memory()

    serialized = (
        DomainSerializer.serialize_memory(
            original
        )
    )

    restored = (
        DomainSerializer.deserialize_memory(
            serialized
        )
    )

    assert isinstance(
        restored,
        ExplorationMemory,
    )

    assert restored.is_executed(
        "hash-A",
        "num7Button",
    )

    assert restored.is_executed(
        "hash-A",
        "plusButton",
    )

    assert restored.is_executed(
        "hash-B",
        "equalButton",
    )

    assert not restored.is_executed(
        "hash-B",
        "num8Button",
    )


def test_loaded_memory_remains_mutable():
    """
    Loaded ExplorationMemory must continue behaving like a normal
    runtime object.

    Persistence must not merely restore data; it must restore usable
    behavior.
    """

    original = create_test_memory()

    serialized = (
        DomainSerializer.serialize_memory(
            original
        )
    )

    restored = (
        DomainSerializer.deserialize_memory(
            serialized
        )
    )

    restored.mark_executed(
        "hash-C",
        "num8Button",
    )

    assert restored.is_executed(
        "hash-C",
        "num8Button",
    )


# =============================================================
# COMPLETE TEST RUNNER
# =============================================================


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_action_serialization_is_json_compatible,
        test_action_round_trip_preserves_all_fields,
        test_state_serialization_is_json_compatible,
        test_state_round_trip_preserves_identity_and_observation,
        test_state_round_trip_reconstructs_nested_actions,
        test_transition_serialization_is_json_compatible,
        test_transition_round_trip_preserves_all_fields,
        test_memory_serialization_is_json_compatible,
        test_memory_serialization_is_deterministic,
        test_memory_round_trip_preserves_exploration_history,
        test_loaded_memory_remains_mutable,
    ]

    print()

    print(
        "===== DOMAIN SERIALIZER TESTS ====="
    )

    print()

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All DomainSerializer tests passed successfully."
    )


if __name__ == "__main__":

    main()