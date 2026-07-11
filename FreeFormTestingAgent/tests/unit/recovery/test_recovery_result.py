"""
Unit tests for RecoveryResult.
"""

from agent.recovery.recovery_result import (
    RecoveryResult,
)


def test_successful_recovery():

    result = RecoveryResult(
        success=True,
        recovered_state_id="STATE-1",
        duration=1.5,
    )

    assert result.success

    assert (
        result.recovered_state_id
        ==
        "STATE-1"
    )

    assert (
        result.duration
        ==
        1.5
    )

    assert (
        result.failure_reason
        is None
    )


def test_failed_recovery():

    result = RecoveryResult(
        success=False,
        recovered_state_id=None,
        duration=2.0,
        failure_reason="Replay failed.",
    )

    assert not result.success

    assert (
        result.recovered_state_id
        is None
    )

    assert (
        result.failure_reason
        ==
        "Replay failed."
    )


def test_invalid_success():

    try:

        RecoveryResult(
            success="yes",
            recovered_state_id=None,
            duration=1,
        )

        assert False

    except ValueError:

        pass


def test_invalid_state_id():

    try:

        RecoveryResult(
            success=True,
            recovered_state_id="",
            duration=1,
        )

        assert False

    except ValueError:

        pass


def test_invalid_duration():

    try:

        RecoveryResult(
            success=True,
            recovered_state_id=None,
            duration=-1,
        )

        assert False

    except ValueError:

        pass


def test_invalid_failure_reason():

    try:

        RecoveryResult(
            success=False,
            recovered_state_id=None,
            duration=1,
            failure_reason="",
        )

        assert False

    except ValueError:

        pass


def main():

    print()

    print(
        "===== RECOVERY RESULT TESTS ====="
    )

    tests = [
        test_successful_recovery,
        test_failed_recovery,
        test_invalid_success,
        test_invalid_state_id,
        test_invalid_duration,
        test_invalid_failure_reason,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RecoveryResult tests passed successfully."
    )


if __name__ == "__main__":

    main()