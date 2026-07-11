"""
Unit tests for RestartRecoveryPolicy.
"""

from agent.failure.failure_record import (
    FailureRecord,
)
from agent.failure.failure_type import (
    FailureType,
)

from agent.recovery.recovery_context import (
    RecoveryContext,
)
from agent.recovery.recovery_execution_result import (
    RecoveryExecutionResult,
)
from agent.recovery.recovery_result import (
    RecoveryResult,
)
from agent.recovery.restart_recovery_policy import (
    RestartRecoveryPolicy,
)


# ============================================================
# Test Doubles
# ============================================================

class Dummy:
    pass


class FakeRecoveryExecutor:

    def __init__(self):

        self.context = None

        self.result = RecoveryExecutionResult(
            success=True,
            window=object(),
            duration=1.0,
        )

    def execute(
        self,
        context,
    ):

        self.context = context

        return self.result


class FailedRecoveryExecutor(
    FakeRecoveryExecutor,
):

    def __init__(self):

        super().__init__()

        self.result = RecoveryExecutionResult(
            success=False,
            window=None,
            duration=2.0,
            error_message="Launch failed.",
        )


# ============================================================
# Helpers
# ============================================================

def make_failure():

    return FailureRecord(

        failure_type=(
            FailureType.APPLICATION_DISAPPEARED
        ),

        message="Calculator disappeared.",

        source_state_id="STATE-1",

        action=None,

        target_state_id=None,

        replay_path=[],

        screenshot_path=None,

        recoverable=True,

        metadata={},
    )


def make_context():

    return RecoveryContext(

        executable="calc.exe",

        window_title="Calculator",

        ui_adapter=Dummy(),

        replay_engine=Dummy(),

        graph=Dummy(),

        memory=Dummy(),
    )


# ============================================================
# Tests
# ============================================================

def test_executor_is_called():

    executor = FakeRecoveryExecutor()

    policy = RestartRecoveryPolicy(
        executor
    )

    context = make_context()

    policy.recover(
        make_failure(),
        context,
    )

    assert (
        executor.context
        is context
    )


def test_successful_execution_returns_success():

    policy = RestartRecoveryPolicy(
        FakeRecoveryExecutor()
    )

    result = policy.recover(
        make_failure(),
        make_context(),
    )

    assert isinstance(
        result,
        RecoveryResult,
    )

    assert result.success


def test_failed_execution_returns_failure():

    policy = RestartRecoveryPolicy(
        FailedRecoveryExecutor()
    )

    result = policy.recover(
        make_failure(),
        make_context(),
    )

    assert not result.success

    assert (
        result.failure_reason
        ==
        "Launch failed."
    )


def main():

    print()

    print(
        "===== RESTART RECOVERY POLICY TESTS ====="
    )

    print()

    tests = [

        test_executor_is_called,

        test_successful_execution_returns_success,

        test_failed_execution_returns_failure,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RestartRecoveryPolicy tests passed successfully."
    )


if __name__ == "__main__":

    main()