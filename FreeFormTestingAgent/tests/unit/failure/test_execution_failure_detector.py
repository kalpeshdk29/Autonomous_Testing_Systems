"""
File:
    test_execution_failure_detector.py

Purpose:
    Verify deterministic conversion of ExplorationStepResult
    outcomes into structured FailureRecord objects.

Coverage:

    REPLAY_FAILED
        → REPLAY_FAILED FailureRecord

    ACTION_EXECUTION_FAILED
        → ACTION_EXECUTION_FAILED FailureRecord

    Successful Step
        → None

    Framework / Control-Flow Outcome
        → None

    Invalid Observation
        → ValueError
"""


from datetime import datetime


from core.models.action import (
    Action,
)

from core.models.action_type import (
    ActionType,
)


from agent.explorer.exploration_step_result import (
    ExplorationStepResult,
)

from agent.failure.execution_failure_detector import (
    ExecutionFailureDetector,
)

from agent.failure.failure_type import (
    FailureType,
)


# =============================================================
# TEST HELPERS
# =============================================================


def create_action() -> Action:
    """
    Create a deterministic action fixture.
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

        description=(
            "Click the Save button."
        ),
    )


# =============================================================
# REPLAY FAILURE TESTS
# =============================================================


def test_replay_failure_creates_failure_record():
    """
    REPLAY_FAILED must produce a structured failure.
    """

    action = create_action()

    result = ExplorationStepResult(
        source_state_id="S1",

        selected_action=action,

        replay_success=False,

        execution_success=False,

        duration=0.0,

        failure_reason="REPLAY_FAILED",
    )

    detector = (
        ExecutionFailureDetector()
    )

    failure = detector.detect(
        result
    )

    assert failure is not None

    assert (
        failure.failure_type
        ==
        FailureType.REPLAY_FAILED
    )

    assert (
        failure.source_state_id
        ==
        "S1"
    )

    assert (
        failure.action
        is
        action
    )

    assert not failure.recoverable


def test_replay_failure_preserves_metadata():
    """
    Replay failure facts must be preserved as structured metadata.
    """

    result = ExplorationStepResult(
        source_state_id="S1",

        selected_action=create_action(),

        replay_success=False,

        execution_success=False,

        duration=1.25,

        failure_reason="REPLAY_FAILED",
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is not None

    assert (
        failure.metadata[
            "failure_reason"
        ]
        ==
        "REPLAY_FAILED"
    )

    assert (
        failure.metadata[
            "replay_success"
        ]
        is False
    )

    assert (
        failure.metadata[
            "execution_success"
        ]
        is False
    )

    assert (
        failure.metadata[
            "duration"
        ]
        ==
        1.25
    )


# =============================================================
# ACTION EXECUTION FAILURE TESTS
# =============================================================


def test_action_execution_failure_creates_failure_record():
    """
    ACTION_EXECUTION_FAILED must produce a structured failure.
    """

    action = create_action()

    result = ExplorationStepResult(
        source_state_id="S2",

        selected_action=action,

        replay_success=True,

        execution_success=False,

        duration=0.75,

        failure_reason=(
            "ACTION_EXECUTION_FAILED"
        ),
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is not None

    assert (
        failure.failure_type
        ==
        FailureType
        .ACTION_EXECUTION_FAILED
    )

    assert (
        failure.source_state_id
        ==
        "S2"
    )

    assert (
        failure.action
        is
        action
    )

    assert failure.recoverable


def test_action_execution_failure_preserves_duration():
    """
    Action execution duration must remain available for future
    timeout analysis and reporting.
    """

    result = ExplorationStepResult(
        source_state_id="S2",

        selected_action=create_action(),

        replay_success=True,

        execution_success=False,

        duration=2.5,

        failure_reason=(
            "ACTION_EXECUTION_FAILED"
        ),
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is not None

    assert (
        failure.metadata["duration"]
        ==
        2.5
    )

    assert (
        failure.metadata[
            "replay_success"
        ]
        is True
    )

    assert (
        failure.metadata[
            "execution_success"
        ]
        is False
    )


# =============================================================
# NON-FAILURE TESTS
# =============================================================


def test_successful_step_returns_none():
    """
    Successful exploration must not create a failure record.
    """

    result = ExplorationStepResult(
        source_state_id="S1",

        selected_action=create_action(),

        target_state_id="S2",

        replay_success=True,

        execution_success=True,

        new_state_discovered=True,

        duration=0.5,

        failure_reason=None,
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is None


def test_source_state_not_found_returns_none():
    """
    Missing graph source state is currently a framework outcome,
    not an application failure.
    """

    result = ExplorationStepResult(
        source_state_id="MISSING",

        failure_reason=(
            "SOURCE_STATE_NOT_FOUND"
        ),
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is None


def test_no_eligible_action_returns_none():
    """
    Exhausted exploration work is not an application failure.
    """

    result = ExplorationStepResult(
        source_state_id="S1",

        failure_reason=(
            "NO_ELIGIBLE_ACTION"
        ),
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is None


def test_source_depth_not_found_returns_none():
    """
    Missing graph depth is a framework consistency problem and is
    not classified by this detector.
    """

    result = ExplorationStepResult(
        source_state_id="S1",

        selected_action=create_action(),

        replay_success=True,

        execution_success=True,

        failure_reason=(
            "SOURCE_DEPTH_NOT_FOUND"
        ),
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is None


def test_unknown_failure_reason_returns_none():
    """
    Unsupported failure reasons must not be misclassified.
    """

    result = ExplorationStepResult(
        source_state_id="S1",

        failure_reason=(
            "UNKNOWN_FAILURE"
        ),
    )

    failure = (
        ExecutionFailureDetector()
        .detect(result)
    )

    assert failure is None


# =============================================================
# VALIDATION TESTS
# =============================================================


def test_invalid_observation_is_rejected():
    """
    Detector input must be an ExplorationStepResult.
    """

    detector = (
        ExecutionFailureDetector()
    )

    try:

        detector.detect(
            {
                "failure_reason":
                "REPLAY_FAILED",
            }
        )

        assert False, (
            "Expected invalid observation "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "ExplorationStepResult"
            in
            str(error)
        )


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


def main():
    """
    Run all ExecutionFailureDetector tests directly.
    """

    print()

    print(
        "===== EXECUTION FAILURE DETECTOR TESTS ====="
    )

    print()

    tests = [
        test_replay_failure_creates_failure_record,
        test_replay_failure_preserves_metadata,

        test_action_execution_failure_creates_failure_record,
        test_action_execution_failure_preserves_duration,

        test_successful_step_returns_none,
        test_source_state_not_found_returns_none,
        test_no_eligible_action_returns_none,
        test_source_depth_not_found_returns_none,
        test_unknown_failure_reason_returns_none,

        test_invalid_observation_is_rejected,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All ExecutionFailureDetector tests "
        "passed successfully."
    )


if __name__ == "__main__":

    main()