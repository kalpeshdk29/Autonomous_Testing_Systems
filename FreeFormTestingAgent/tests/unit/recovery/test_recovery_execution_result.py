"""
Unit tests for RecoveryExecutionResult.
"""

from agent.recovery.recovery_execution_result import (
    RecoveryExecutionResult,
)


class DummyWindow:
    pass


def test_successful_execution():

    window = DummyWindow()

    result = RecoveryExecutionResult(
        success=True,

        window=window,

        duration=1.5,
    )

    assert result.success

    assert result.window is window

    assert result.duration == 1.5

    assert result.error_message is None


def test_failed_execution():

    result = RecoveryExecutionResult(
        success=False,

        window=None,

        duration=2.0,

        error_message="Launch failed.",
    )

    assert not result.success

    assert result.window is None

    assert result.error_message == "Launch failed."


def test_invalid_success():

    try:

        RecoveryExecutionResult(
            success="yes",

            window=None,

            duration=1,
        )

        assert False

    except ValueError:

        pass


def test_invalid_duration():

    try:

        RecoveryExecutionResult(
            success=True,

            window=None,

            duration=-1,
        )

        assert False

    except ValueError:

        pass


def test_invalid_error_message():

    try:

        RecoveryExecutionResult(
            success=False,

            window=None,

            duration=1,

            error_message="",
        )

        assert False

    except ValueError:

        pass


def main():

    print()

    print(
        "===== RECOVERY EXECUTION RESULT TESTS ====="
    )

    print()

    tests = [

        test_successful_execution,

        test_failed_execution,

        test_invalid_success,

        test_invalid_duration,

        test_invalid_error_message,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RecoveryExecutionResult tests passed successfully."
    )


if __name__ == "__main__":

    main()