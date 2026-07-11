"""
Unit tests for RecoveryManager.
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

from agent.recovery.recovery_manager import (
    RecoveryManager,
)

from agent.recovery.recovery_result import (
    RecoveryResult,
)


# ============================================================
# Test doubles
# ============================================================

class Dummy:
    pass


class FakeRecoveryPolicy:

    def __init__(self):

        self.failure = None
        self.context = None

    def recover(
        self,
        failure,
        context,
    ):

        self.failure = failure
        self.context = context

        return RecoveryResult(
            success=True,
            recovered_state_id="STATE-1",
            duration=1.0,
        )


# ============================================================
# Helpers
# ============================================================

def make_failure():

    return FailureRecord(

        failure_type=(
            FailureType.APPLICATION_DISAPPEARED
        ),

        message="Application disappeared.",

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

def test_correct_policy_is_selected():

    policy = FakeRecoveryPolicy()

    manager = RecoveryManager(

        {

            FailureType.APPLICATION_DISAPPEARED:
                policy

        }

    )

    manager.recover(

        make_failure(),

        make_context(),

    )

    assert policy.failure is not None


def test_failure_is_forwarded():

    policy = FakeRecoveryPolicy()

    manager = RecoveryManager(

        {

            FailureType.APPLICATION_DISAPPEARED:
                policy

        }

    )

    failure = make_failure()

    manager.recover(

        failure,

        make_context(),

    )

    assert policy.failure is failure


def test_context_is_forwarded():

    policy = FakeRecoveryPolicy()

    manager = RecoveryManager(

        {

            FailureType.APPLICATION_DISAPPEARED:
                policy

        }

    )

    context = make_context()

    manager.recover(

        make_failure(),

        context,

    )

    assert policy.context is context


def test_policy_result_is_returned():

    manager = RecoveryManager(

        {

            FailureType.APPLICATION_DISAPPEARED:
                FakeRecoveryPolicy()

        }

    )

    result = manager.recover(

        make_failure(),

        make_context(),

    )

    assert result.success


def test_unknown_failure_returns_failed_result():

    manager = RecoveryManager({})

    result = manager.recover(

        make_failure(),

        make_context(),

    )

    assert not result.success

    assert result.failure_reason == (
        "No recovery policy registered."
    )


def main():

    print()

    print(
        "===== RECOVERY MANAGER TESTS ====="
    )

    print()

    tests = [

        test_correct_policy_is_selected,

        test_failure_is_forwarded,

        test_context_is_forwarded,

        test_policy_result_is_returned,

        test_unknown_failure_returns_failed_result,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RecoveryManager tests passed successfully."
    )


if __name__ == "__main__":

    main()