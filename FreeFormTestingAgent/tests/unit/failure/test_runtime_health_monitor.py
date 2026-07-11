"""
File:
    test_runtime_health_monitor.py

Purpose:
    Verify deterministic runtime-health monitoring.

Coverage:

    Healthy observation
        → None

    Failed observation
        → FailureRecord

    Source state
        → passed to probe

    Observation
        → passed to detector

    Dependencies
        → validated

    Source state
        → validated
"""

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.failure.process_health_observation import (
    ProcessHealthObservation,
)

from agent.failure.runtime_health_monitor import (
    RuntimeHealthMonitor,
)


# =============================================================
# TEST DOUBLES
# =============================================================


class FakeProbe:

    def __init__(
        self,
        observation,
    ):

        self.observation = observation

        self.calls = []

    def observe(
        self,
        source_state_id,
    ):

        self.calls.append(
            source_state_id
        )

        return self.observation


class FakeDetector:

    def __init__(
        self,
        failure,
    ):

        self.failure = failure

        self.calls = []

    def detect(
        self,
        observation,
    ):

        self.calls.append(
            observation
        )

        return self.failure


def make_observation(
    is_running: bool,
):
    """
    Create deterministic process-health observation.
    """

    return ProcessHealthObservation(
        process_name=(
            "CalculatorApp.exe"
        ),

        process_id=1234,

        is_running=is_running,

        source_state_id="S1",
    )


def make_failure():
    """
    Create deterministic application disappearance failure.
    """

    return FailureRecord(
        failure_type=(
            FailureType
            .APPLICATION_DISAPPEARED
        ),

        message=(
            "Application disappeared."
        ),

        source_state_id="S1",

        action=None,

        target_state_id=None,

        replay_path=[],

        screenshot_path=None,

        recoverable=True,

        metadata={
            "process_id": 1234,
        },
    )


# =============================================================
# HEALTH CHECK TESTS
# =============================================================


def test_healthy_runtime_returns_none():

    observation = make_observation(
        is_running=True
    )

    probe = FakeProbe(
        observation
    )

    detector = FakeDetector(
        failure=None
    )

    monitor = RuntimeHealthMonitor(
        probe=probe,

        detector=detector,
    )

    result = monitor.check(
        source_state_id="S1"
    )

    assert result is None


def test_failed_runtime_returns_failure_record():

    observation = make_observation(
        is_running=False
    )

    failure = make_failure()

    monitor = RuntimeHealthMonitor(
        probe=FakeProbe(
            observation
        ),

        detector=FakeDetector(
            failure
        ),
    )

    result = monitor.check(
        source_state_id="S1"
    )

    assert result is failure

    assert (
        result.failure_type
        ==
        FailureType
        .APPLICATION_DISAPPEARED
    )


def test_source_state_is_passed_to_probe():

    observation = make_observation(
        is_running=True
    )

    probe = FakeProbe(
        observation
    )

    monitor = RuntimeHealthMonitor(
        probe=probe,

        detector=FakeDetector(
            failure=None
        ),
    )

    monitor.check(
        source_state_id="STATE-123"
    )

    assert (
        probe.calls
        ==
        [
            "STATE-123"
        ]
    )


def test_probe_observation_is_passed_to_detector():

    observation = make_observation(
        is_running=False
    )

    detector = FakeDetector(
        failure=make_failure()
    )

    monitor = RuntimeHealthMonitor(
        probe=FakeProbe(
            observation
        ),

        detector=detector,
    )

    monitor.check(
        source_state_id="S1"
    )

    assert len(
        detector.calls
    ) == 1

    assert (
        detector.calls[0]
        is
        observation
    )


def test_probe_is_called_once_per_check():

    observation = make_observation(
        is_running=True
    )

    probe = FakeProbe(
        observation
    )

    monitor = RuntimeHealthMonitor(
        probe=probe,

        detector=FakeDetector(
            failure=None
        ),
    )

    monitor.check(
        source_state_id="S1"
    )

    assert len(
        probe.calls
    ) == 1


def test_detector_is_called_once_per_check():

    observation = make_observation(
        is_running=True
    )

    detector = FakeDetector(
        failure=None
    )

    monitor = RuntimeHealthMonitor(
        probe=FakeProbe(
            observation
        ),

        detector=detector,
    )

    monitor.check(
        source_state_id="S1"
    )

    assert len(
        detector.calls
    ) == 1


# =============================================================
# VALIDATION TESTS
# =============================================================


def test_missing_probe_is_rejected():

    try:

        RuntimeHealthMonitor(
            probe=None,

            detector=FakeDetector(
                failure=None
            ),
        )

        assert False, (
            "Expected missing probe "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "probe"
            in
            str(error)
        )


def test_probe_without_observe_is_rejected():

    class InvalidProbe:
        pass

    try:

        RuntimeHealthMonitor(
            probe=InvalidProbe(),

            detector=FakeDetector(
                failure=None
            ),
        )

        assert False, (
            "Expected invalid probe "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "observe"
            in
            str(error)
        )


def test_missing_detector_is_rejected():

    try:

        RuntimeHealthMonitor(
            probe=FakeProbe(
                make_observation(
                    is_running=True
                )
            ),

            detector=None,
        )

        assert False, (
            "Expected missing detector "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "detector"
            in
            str(error)
        )


def test_detector_without_detect_is_rejected():

    class InvalidDetector:
        pass

    try:

        RuntimeHealthMonitor(
            probe=FakeProbe(
                make_observation(
                    is_running=True
                )
            ),

            detector=InvalidDetector(),
        )

        assert False, (
            "Expected invalid detector "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "detect"
            in
            str(error)
        )


def test_empty_source_state_id_is_rejected():

    monitor = RuntimeHealthMonitor(
        probe=FakeProbe(
            make_observation(
                is_running=True
            )
        ),

        detector=FakeDetector(
            failure=None
        ),
    )

    try:

        monitor.check(
            source_state_id=""
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


def test_non_string_source_state_id_is_rejected():

    monitor = RuntimeHealthMonitor(
        probe=FakeProbe(
            make_observation(
                is_running=True
            )
        ),

        detector=FakeDetector(
            failure=None
        ),
    )

    try:

        monitor.check(
            source_state_id=123
        )

        assert False, (
            "Expected invalid source state ID "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "source_state_id"
            in
            str(error)
        )


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


def main():

    print()

    print(
        "===== RUNTIME HEALTH MONITOR TESTS ====="
    )

    print()

    tests = [
        test_healthy_runtime_returns_none,

        test_failed_runtime_returns_failure_record,

        test_source_state_is_passed_to_probe,

        test_probe_observation_is_passed_to_detector,

        test_probe_is_called_once_per_check,

        test_detector_is_called_once_per_check,

        test_missing_probe_is_rejected,

        test_probe_without_observe_is_rejected,

        test_missing_detector_is_rejected,

        test_detector_without_detect_is_rejected,

        test_empty_source_state_id_is_rejected,

        test_non_string_source_state_id_is_rejected,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RuntimeHealthMonitor tests "
        "passed successfully."
    )


if __name__ == "__main__":

    main()