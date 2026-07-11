"""
File:
    test_application_disappeared_detector.py

Purpose:
    Verify deterministic detection of application process
    disappearance.

Coverage:

    Running process
        → None

    Missing process
        → APPLICATION_DISAPPEARED

    Process identity
        → preserved in metadata

    Source state
        → preserved

    Missing process ID
        → supported

    Invalid observation
        → rejected

    Observation validation
        → enforced
"""

from agent.failure.application_disappeared_detector import (
    ApplicationDisappearedDetector,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.failure.process_health_observation import (
    ProcessHealthObservation,
)


# =============================================================
# DETECTION TESTS
# =============================================================


def test_running_application_returns_none():
    """
    A healthy running process must not create a failure.
    """

    observation = ProcessHealthObservation(
        process_name="calc.exe",

        process_id=1234,

        is_running=True,

        source_state_id="S1",
    )

    failure = (
        ApplicationDisappearedDetector()
        .detect(
            observation
        )
    )

    assert failure is None


def test_missing_application_creates_failure_record():
    """
    A disappeared process must create a structured failure.
    """

    observation = ProcessHealthObservation(
        process_name="calc.exe",

        process_id=1234,

        is_running=False,

        source_state_id="S1",
    )

    failure = (
        ApplicationDisappearedDetector()
        .detect(
            observation
        )
    )

    assert failure is not None

    assert (
        failure.failure_type
        ==
        FailureType
        .APPLICATION_DISAPPEARED
    )


def test_failure_preserves_source_state():
    """
    Failure must identify the exploration state active when the
    application disappeared.
    """

    observation = ProcessHealthObservation(
        process_name="calc.exe",

        process_id=1234,

        is_running=False,

        source_state_id="STATE-123",
    )

    failure = (
        ApplicationDisappearedDetector()
        .detect(
            observation
        )
    )

    assert failure is not None

    assert (
        failure.source_state_id
        ==
        "STATE-123"
    )


def test_failure_preserves_process_metadata():
    """
    Process identity and probe details must remain available as
    structured metadata.
    """

    observation = ProcessHealthObservation(
        process_name="calc.exe",

        process_id=9876,

        is_running=False,

        source_state_id="S1",

        details=(
            "Process lookup returned no "
            "matching running process."
        ),
    )

    failure = (
        ApplicationDisappearedDetector()
        .detect(
            observation
        )
    )

    assert failure is not None

    assert (
        failure.metadata[
            "process_name"
        ]
        ==
        "calc.exe"
    )

    assert (
        failure.metadata[
            "process_id"
        ]
        ==
        9876
    )

    assert (
        failure.metadata[
            "is_running"
        ]
        is False
    )

    assert (
        failure.metadata[
            "details"
        ]
        ==
        (
            "Process lookup returned no "
            "matching running process."
        )
    )


def test_missing_process_id_is_supported():
    """
    The detector must still report disappearance when a process ID
    was never resolved.
    """

    observation = ProcessHealthObservation(
        process_name="calc.exe",

        process_id=None,

        is_running=False,

        source_state_id="S1",
    )

    failure = (
        ApplicationDisappearedDetector()
        .detect(
            observation
        )
    )

    assert failure is not None

    assert (
        failure.failure_type
        ==
        FailureType
        .APPLICATION_DISAPPEARED
    )

    assert (
        failure.metadata[
            "process_id"
        ]
        is None
    )


def test_application_disappearance_is_recoverable():
    """
    Application disappearance is initially classified as
    recoverable because a future recovery policy may restart and
    replay the application.
    """

    observation = ProcessHealthObservation(
        process_name="calc.exe",

        process_id=1234,

        is_running=False,

        source_state_id="S1",
    )

    failure = (
        ApplicationDisappearedDetector()
        .detect(
            observation
        )
    )

    assert failure is not None

    assert failure.recoverable


# =============================================================
# DETECTOR VALIDATION TESTS
# =============================================================


def test_invalid_detector_observation_is_rejected():
    """
    Detector input must be a ProcessHealthObservation.
    """

    detector = (
        ApplicationDisappearedDetector()
    )

    try:

        detector.detect(
            {
                "process_name": "calc.exe",

                "is_running": False,
            }
        )

        assert False, (
            "Expected invalid observation "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "ProcessHealthObservation"
            in
            str(error)
        )


# =============================================================
# OBSERVATION VALIDATION TESTS
# =============================================================


def test_empty_process_name_is_rejected():

    try:

        ProcessHealthObservation(
            process_name="",

            process_id=1234,

            is_running=True,

            source_state_id="S1",
        )

        assert False, (
            "Expected empty process name "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "process_name"
            in
            str(error)
        )


def test_invalid_process_id_is_rejected():

    try:

        ProcessHealthObservation(
            process_name="calc.exe",

            process_id=0,

            is_running=True,

            source_state_id="S1",
        )

        assert False, (
            "Expected invalid process ID "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "process_id"
            in
            str(error)
        )


def test_empty_source_state_id_is_rejected():

    try:

        ProcessHealthObservation(
            process_name="calc.exe",

            process_id=1234,

            is_running=True,

            source_state_id="",
        )

        assert False, (
            "Expected empty source state ID "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "source_state_id"
            in
            str(error)
        )


def test_invalid_running_value_is_rejected():

    try:

        ProcessHealthObservation(
            process_name="calc.exe",

            process_id=1234,

            is_running="no",

            source_state_id="S1",
        )

        assert False, (
            "Expected invalid is_running "
            "value to be rejected."
        )

    except ValueError as error:

        assert (
            "is_running"
            in
            str(error)
        )


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


def main():
    """
    Run all ApplicationDisappearedDetector tests directly.
    """

    print()

    print(
        "===== APPLICATION DISAPPEARED "
        "DETECTOR TESTS ====="
    )

    print()

    tests = [
        test_running_application_returns_none,

        test_missing_application_creates_failure_record,

        test_failure_preserves_source_state,

        test_failure_preserves_process_metadata,

        test_missing_process_id_is_supported,

        test_application_disappearance_is_recoverable,

        test_invalid_detector_observation_is_rejected,

        test_empty_process_name_is_rejected,

        test_invalid_process_id_is_rejected,

        test_empty_source_state_id_is_rejected,

        test_invalid_running_value_is_rejected,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All ApplicationDisappearedDetector "
        "tests passed successfully."
    )


if __name__ == "__main__":

    main()