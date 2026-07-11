"""
File:
    test_process_health_probe.py

Purpose:
    Verify deterministic process-health observation.

Coverage:

    poll() returns None
        → running observation

    poll() returns exit code
        → disappeared observation

    process identity
        → preserved

    source state
        → preserved

    invalid dependencies
        → rejected
"""

from agent.failure.process_health_probe import (
    ProcessHealthProbe,
)


# =============================================================
# TEST DOUBLE
# =============================================================


class FakeProcess:
    """
    Deterministic process-like object.
    """

    def __init__(
        self,
        pid: int,
        return_code,
    ):

        self.pid = pid

        self.return_code = (
            return_code
        )

        self.poll_calls = 0

    def poll(
        self,
    ):

        self.poll_calls += 1

        return self.return_code


# =============================================================
# OBSERVATION TESTS
# =============================================================


def test_running_process_creates_running_observation():

    process = FakeProcess(
        pid=1234,

        return_code=None,
    )

    probe = ProcessHealthProbe(
        process_name="calc.exe",

        process=process,
    )

    observation = probe.observe(
        source_state_id="S1"
    )

    assert observation.is_running

    assert (
        process.poll_calls
        ==
        1
    )


def test_terminated_process_creates_missing_observation():

    process = FakeProcess(
        pid=1234,

        return_code=1,
    )

    probe = ProcessHealthProbe(
        process_name="calc.exe",

        process=process,
    )

    observation = probe.observe(
        source_state_id="S1"
    )

    assert (
        observation.is_running
        is False
    )


def test_observation_preserves_process_identity():

    process = FakeProcess(
        pid=9876,

        return_code=None,
    )

    probe = ProcessHealthProbe(
        process_name="CalculatorApp.exe",

        process=process,
    )

    observation = probe.observe(
        source_state_id="S1"
    )

    assert (
        observation.process_name
        ==
        "CalculatorApp.exe"
    )

    assert (
        observation.process_id
        ==
        9876
    )


def test_observation_preserves_source_state():

    process = FakeProcess(
        pid=1234,

        return_code=None,
    )

    probe = ProcessHealthProbe(
        process_name="calc.exe",

        process=process,
    )

    observation = probe.observe(
        source_state_id=(
            "STATE-123"
        )
    )

    assert (
        observation.source_state_id
        ==
        "STATE-123"
    )


def test_running_process_has_health_details():

    process = FakeProcess(
        pid=1234,

        return_code=None,
    )

    observation = (
        ProcessHealthProbe(
            process_name="calc.exe",

            process=process,
        )
        .observe(
            source_state_id="S1"
        )
    )

    assert (
        observation.details
        ==
        "Tracked process is running."
    )


def test_terminated_process_preserves_exit_code():

    process = FakeProcess(
        pid=1234,

        return_code=5,
    )

    observation = (
        ProcessHealthProbe(
            process_name="calc.exe",

            process=process,
        )
        .observe(
            source_state_id="S1"
        )
    )

    assert (
        "5"
        in
        observation.details
    )


# =============================================================
# VALIDATION TESTS
# =============================================================


def test_empty_process_name_is_rejected():

    process = FakeProcess(
        pid=1234,

        return_code=None,
    )

    try:

        ProcessHealthProbe(
            process_name="",

            process=process,
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


def test_missing_process_is_rejected():

    try:

        ProcessHealthProbe(
            process_name="calc.exe",

            process=None,
        )

        assert False, (
            "Expected missing process "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "process"
            in
            str(error)
        )


def test_process_without_pid_is_rejected():

    class ProcessWithoutPid:

        def poll(
            self,
        ):

            return None

    try:

        ProcessHealthProbe(
            process_name="calc.exe",

            process=(
                ProcessWithoutPid()
            ),
        )

        assert False, (
            "Expected process without PID "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "pid"
            in
            str(error)
        )


def test_process_without_poll_is_rejected():

    class ProcessWithoutPoll:

        pid = 1234

    try:

        ProcessHealthProbe(
            process_name="calc.exe",

            process=(
                ProcessWithoutPoll()
            ),
        )

        assert False, (
            "Expected process without poll "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "poll"
            in
            str(error)
        )


def test_invalid_process_pid_is_rejected():

    process = FakeProcess(
        pid=0,

        return_code=None,
    )

    try:

        ProcessHealthProbe(
            process_name="calc.exe",

            process=process,
        )

        assert False, (
            "Expected invalid PID "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "process.pid"
            in
            str(error)
        )


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


def main():

    print()

    print(
        "===== PROCESS HEALTH PROBE TESTS ====="
    )

    print()

    tests = [
        test_running_process_creates_running_observation,

        test_terminated_process_creates_missing_observation,

        test_observation_preserves_process_identity,

        test_observation_preserves_source_state,

        test_running_process_has_health_details,

        test_terminated_process_preserves_exit_code,

        test_empty_process_name_is_rejected,

        test_missing_process_is_rejected,

        test_process_without_pid_is_rejected,

        test_process_without_poll_is_rejected,

        test_invalid_process_pid_is_rejected,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All ProcessHealthProbe tests "
        "passed successfully."
    )


if __name__ == "__main__":

    main()