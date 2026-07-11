"""
Unit tests for RecoveryPolicy.
"""

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.recovery.recovery_policy import (
    RecoveryPolicy,
)

from agent.recovery.recovery_result import (
    RecoveryResult,
)

from agent.recovery.recovery_context import (
    RecoveryContext,
)

class FakeRecoveryPolicy(
    RecoveryPolicy,
):

    def recover(
        self,
        failure,
        context,
    ):

        return RecoveryResult(
            success=True,
            recovered_state_id="STATE-1",
            duration=1.25,
        )


def make_failure():

    return FailureRecord(
        failure_type=(
            FailureType
            .APPLICATION_DISAPPEARED
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


def test_policy_returns_recovery_result():

    policy = FakeRecoveryPolicy()

    result = policy.recover(
    make_failure(),
    make_context(),
)

    assert isinstance(
        result,
        RecoveryResult,
    )


def test_context_is_passed_to_policy():

    class RecordingPolicy(
        RecoveryPolicy,
    ):

        def __init__(self):

            self.context = None

        def recover(
            self,
            failure,
            context,
        ):

            self.context = context

            return RecoveryResult(
                success=True,
                recovered_state_id=None,
                duration=0,
            )

    context = make_context()

    policy = RecordingPolicy()

    policy.recover(
        make_failure(),
        context,
    )

    assert (
        policy.context
        is context
    )

def test_failure_is_passed_to_policy():

    failure = make_failure()

    context = make_context()

    policy = RecordingPolicy()

    policy.recover(
        failure,
        context,
    )

    assert (
        policy.failure
        is failure
    )

def test_successful_recovery():

    policy = FakeRecoveryPolicy()

    result = policy.recover(
    make_failure(),
    make_context(),
)

    assert result.success

    assert (
        result.recovered_state_id
        ==
        "STATE-1"
    )

class Dummy:
    pass


def make_context():

    return RecoveryContext(
        executable="calc.exe",

        window_title="Calculator",

        ui_adapter=Dummy(),

        replay_engine=Dummy(),

        graph=Dummy(),

        memory=Dummy(),
    )


class RecordingPolicy(
    RecoveryPolicy,
):

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
            recovered_state_id=None,
            duration=0,
        )


def test_recovery_policy_is_abstract():

    try:

        RecoveryPolicy()

        assert False

    except TypeError:

        pass


def main():

    print()

    print(
        "===== RECOVERY POLICY TESTS ====="
    )

    print()

    tests = [

        test_policy_returns_recovery_result,

        test_successful_recovery,

        test_failure_is_passed_to_policy,

        test_context_is_passed_to_policy,

        test_recovery_policy_is_abstract,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RecoveryPolicy tests passed successfully."
    )


if __name__ == "__main__":

    main()