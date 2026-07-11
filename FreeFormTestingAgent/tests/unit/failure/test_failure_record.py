"""
File:
    test_failure_record.py

Purpose:
    Verify the stable deterministic failure-domain contract.

Coverage:

    FailureType
        ↓
    FailureRecord
        ↓
    Identity
    Context
    Action
    Replay Path
    Evidence
    Recovery Information
    Metadata
    Validation
"""

from datetime import datetime


from core.models.action import (
    Action,
)

from core.models.action_type import (
    ActionType,
)

from core.models.transition import (
    Transition,
)


from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_type import (
    FailureType,
)

# =============================================================
# TEST HELPERS
# =============================================================


def create_action() -> Action:
    """
    Create a deterministic test action.
    """

    return Action(
        action_id="ACTION-1",
        action_type=ActionType.CLICK,
        target="saveButton",
        value=None,
        timestamp=datetime(
            2026,
            7,
            10,
            10,
            0,
            0,
        ),
        description=("Click the Save button."),
    )


def create_transition(
    source_state: str,
    target_state: str,
    action: Action,
) -> Transition:
    """
    Create a deterministic replay transition.
    """

    return Transition(
        source_state=source_state,
        target_state=target_state,
        action=action,
        success=True,
        duration=0.5,
    )


def create_failure_record() -> FailureRecord:
    """
    Create a complete deterministic failure record.
    """

    action = create_action()

    transition = create_transition(
        source_state="S0",
        target_state="S1",
        action=action,
    )

    return FailureRecord(
        failure_id="FAILURE-1",
        failure_type=(FailureType.ACTION_EXECUTION_FAILED),
        message=("Save action could not be executed."),
        timestamp=datetime(
            2026,
            7,
            10,
            10,
            5,
            0,
        ),
        source_state_id="S1",
        action=action,
        target_state_id=None,
        replay_path=[
            transition,
        ],
        screenshot_path=("storage/screenshots/" "session-1/failure-1.png"),
        recoverable=True,
        metadata={
            "executor_error": ("Control not available."),
        },
    )


# =============================================================
# FAILURE TYPE TESTS
# =============================================================


def test_failure_types_have_stable_values():
    """
    Failure types must expose stable persistence-safe values.
    """

    assert FailureType.ACTION_EXECUTION_FAILED.value == "ACTION_EXECUTION_FAILED"

    assert FailureType.ACTION_TIMEOUT.value == "ACTION_TIMEOUT"

    assert FailureType.REPLAY_FAILED.value == "REPLAY_FAILED"

    assert FailureType.REPLAY_STATE_MISMATCH.value == "REPLAY_STATE_MISMATCH"

    assert FailureType.APPLICATION_DISAPPEARED.value == "APPLICATION_DISAPPEARED"

    assert FailureType.WINDOW_DISAPPEARED.value == "WINDOW_DISAPPEARED"

    assert FailureType.STATE_CAPTURE_FAILED.value == "STATE_CAPTURE_FAILED"

    assert FailureType.UNEXPECTED_ERROR_DIALOG.value == "UNEXPECTED_ERROR_DIALOG"


# =============================================================
# BASIC FAILURE RECORD TESTS
# =============================================================


def test_failure_record_preserves_required_fields():
    """
    Core failure identity and classification must be preserved.
    """

    record = create_failure_record()

    assert record.failure_id == "FAILURE-1"

    assert record.failure_type == FailureType.ACTION_EXECUTION_FAILED

    assert record.message == "Save action could not be executed."

    assert record.source_state_id == "S1"


def test_failure_record_preserves_timestamp():
    """
    Failure occurrence time must be preserved.
    """

    record = create_failure_record()

    assert record.timestamp == datetime(
        2026,
        7,
        10,
        10,
        5,
        0,
    )


def test_failure_record_preserves_action():
    """
    The action associated with the failure must be preserved.
    """

    record = create_failure_record()

    assert record.action is not None

    assert record.action.action_id == "ACTION-1"

    assert record.action.target == "saveButton"


def test_failure_record_preserves_target_state():
    """
    Target state context must be preserved when available.
    """

    record = FailureRecord(
        failure_type=(FailureType.REPLAY_STATE_MISMATCH),
        message=("Replay reached an unexpected state."),
        source_state_id="S0",
        target_state_id="EXPECTED-S1",
    )

    assert record.target_state_id == "EXPECTED-S1"


# =============================================================
# REPRODUCTION CONTEXT TESTS
# =============================================================


def test_failure_record_preserves_replay_path():
    """
    Replay transitions must be preserved in execution order.
    """

    record = create_failure_record()

    assert len(record.replay_path) == 1

    transition = record.replay_path[0]

    assert transition.source_state == "S0"

    assert transition.target_state == "S1"

    assert transition.action.target == "saveButton"


def test_failure_record_defaults_to_empty_replay_path():
    """
    Failures without replay context must receive an independent
    empty path.
    """

    first = FailureRecord(
        failure_type=(FailureType.APPLICATION_DISAPPEARED),
        message=("Application disappeared."),
        source_state_id="S0",
    )

    second = FailureRecord(
        failure_type=(FailureType.WINDOW_DISAPPEARED),
        message=("Window disappeared."),
        source_state_id="S1",
    )

    assert first.replay_path == []

    assert second.replay_path == []

    assert first.replay_path is not second.replay_path


# =============================================================
# EVIDENCE AND RECOVERY TESTS
# =============================================================


def test_failure_record_preserves_screenshot_path():
    """
    Durable screenshot evidence location must be preserved.
    """

    record = create_failure_record()

    assert record.screenshot_path == "storage/screenshots/" "session-1/failure-1.png"


def test_failure_record_preserves_recoverable_flag():
    """
    Recovery information must be preserved.
    """

    record = create_failure_record()

    assert record.recoverable


def test_failure_record_defaults_to_not_recoverable():
    """
    Unknown failures must default to the safer non-recoverable
    classification.
    """

    record = FailureRecord(
        failure_type=(FailureType.APPLICATION_DISAPPEARED),
        message=("Application disappeared."),
        source_state_id="S0",
    )

    assert not record.recoverable


# =============================================================
# METADATA TESTS
# =============================================================


def test_failure_record_preserves_metadata():
    """
    Detector-specific structured information must be preserved.
    """

    record = create_failure_record()

    assert record.metadata["executor_error"] == "Control not available."


def test_failure_records_have_independent_metadata():
    """
    Mutable metadata defaults must never be shared.
    """

    first = FailureRecord(
        failure_type=(FailureType.ACTION_TIMEOUT),
        message=("Action timed out."),
        source_state_id="S0",
    )

    second = FailureRecord(
        failure_type=(FailureType.ACTION_TIMEOUT),
        message=("Another action timed out."),
        source_state_id="S1",
    )

    first.metadata["timeout"] = 10

    assert "timeout" not in second.metadata


# =============================================================
# IDENTITY TESTS
# =============================================================


def test_failure_ids_are_generated_automatically():
    """
    New failure occurrences must receive unique identities.
    """

    first = FailureRecord(
        failure_type=(FailureType.ACTION_EXECUTION_FAILED),
        message=("First failure."),
        source_state_id="S0",
    )

    second = FailureRecord(
        failure_type=(FailureType.ACTION_EXECUTION_FAILED),
        message=("Second failure."),
        source_state_id="S0",
    )

    assert first.failure_id

    assert second.failure_id

    assert first.failure_id != second.failure_id


def test_failure_timestamp_is_generated_automatically():
    """
    New failures must receive an occurrence timestamp.
    """

    before = datetime.now()

    record = FailureRecord(
        failure_type=(FailureType.STATE_CAPTURE_FAILED),
        message=("State capture failed."),
        source_state_id="S0",
    )

    after = datetime.now()

    assert before <= record.timestamp <= after


# =============================================================
# VALIDATION TESTS
# =============================================================


def test_invalid_failure_type_is_rejected():
    """
    failure_type must be a FailureType.
    """

    try:

        FailureRecord(
            failure_type=("ACTION_EXECUTION_FAILED"),
            message=("Action failed."),
            source_state_id="S0",
        )

        assert False, "Expected invalid failure type " "to be rejected."

    except ValueError as error:

        assert "failure_type" in str(error)


def test_empty_message_is_rejected():
    """
    Failures must contain a meaningful explanation.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.ACTION_EXECUTION_FAILED),
            message="   ",
            source_state_id="S0",
        )

        assert False, "Expected empty message " "to be rejected."

    except ValueError as error:

        assert "message" in str(error)


def test_empty_source_state_id_is_rejected():
    """
    Failure records must identify their source graph state.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.ACTION_EXECUTION_FAILED),
            message=("Action failed."),
            source_state_id="",
        )

        assert False, "Expected empty source state " "to be rejected."

    except ValueError as error:

        assert "source_state_id" in str(error)


def test_invalid_action_is_rejected():
    """
    action must be an Action or None.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.ACTION_EXECUTION_FAILED),
            message=("Action failed."),
            source_state_id="S0",
            action="CLICK(saveButton)",
        )

        assert False, "Expected invalid action " "to be rejected."

    except ValueError as error:

        assert "action" in str(error)


def test_invalid_replay_path_is_rejected():
    """
    replay_path must be a list.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.REPLAY_FAILED),
            message=("Replay failed."),
            source_state_id="S0",
            replay_path="S0 -> S1",
        )

        assert False, "Expected invalid replay path " "to be rejected."

    except ValueError as error:

        assert "replay_path" in str(error)


def test_non_transition_in_replay_path_is_rejected():
    """
    Every replay-path entry must be a Transition.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.REPLAY_FAILED),
            message=("Replay failed."),
            source_state_id="S0",
            replay_path=[
                "S0 -> S1",
            ],
        )

        assert False, "Expected invalid replay-path " "entry to be rejected."

    except ValueError as error:

        assert "Transition" in str(error)


def test_invalid_recoverable_value_is_rejected():
    """
    recoverable must be a bool.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.ACTION_EXECUTION_FAILED),
            message=("Action failed."),
            source_state_id="S0",
            recoverable="yes",
        )

        assert False, "Expected invalid recoverable " "value to be rejected."

    except ValueError as error:

        assert "recoverable" in str(error)


def test_invalid_metadata_is_rejected():
    """
    metadata must be a dictionary.
    """

    try:

        FailureRecord(
            failure_type=(FailureType.STATE_CAPTURE_FAILED),
            message=("State capture failed."),
            source_state_id="S0",
            metadata=[
                "capture error",
            ],
        )

        assert False, "Expected invalid metadata " "to be rejected."

    except ValueError as error:

        assert "metadata" in str(error)


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


def main():
    """
    Run all FailureRecord tests directly.
    """

    print()

    print("===== FAILURE RECORD TESTS =====")

    print()

    tests = [
        test_failure_types_have_stable_values,
        test_failure_record_preserves_required_fields,
        test_failure_record_preserves_timestamp,
        test_failure_record_preserves_action,
        test_failure_record_preserves_target_state,
        test_failure_record_preserves_replay_path,
        test_failure_record_defaults_to_empty_replay_path,
        test_failure_record_preserves_screenshot_path,
        test_failure_record_preserves_recoverable_flag,
        test_failure_record_defaults_to_not_recoverable,
        test_failure_record_preserves_metadata,
        test_failure_records_have_independent_metadata,
        test_failure_ids_are_generated_automatically,
        test_failure_timestamp_is_generated_automatically,
        test_invalid_failure_type_is_rejected,
        test_empty_message_is_rejected,
        test_empty_source_state_id_is_rejected,
        test_invalid_action_is_rejected,
        test_invalid_replay_path_is_rejected,
        test_non_transition_in_replay_path_is_rejected,
        test_invalid_recoverable_value_is_rejected,
        test_invalid_metadata_is_rejected,
    ]

    for test in tests:

        test()

        print(f"PASS: {test.__name__}")

    print()

    print("All FailureRecord tests passed " "successfully.")


if __name__ == "__main__":

    main()
