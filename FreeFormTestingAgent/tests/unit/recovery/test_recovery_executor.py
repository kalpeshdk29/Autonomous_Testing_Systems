"""
Unit tests for RecoveryExecutor.
"""

from agent.recovery.recovery_context import (
    RecoveryContext,
)

from agent.recovery.recovery_execution_result import (
    RecoveryExecutionResult,
)

from agent.recovery.recovery_executor import (
    RecoveryExecutor,
)

from agent.failure.failure_record import (
    FailureRecord,
)
from agent.failure.failure_type import (
    FailureType,
)

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


# ============================================================
# Test Doubles
# ============================================================

class Dummy:
    pass


class FakeUIAdapter:

    def __init__(self):

        self.launch_calls = []

        self.connect_calls = []

        self.window = object()

    def launch_application(
        self,
        executable,
    ):

        self.launch_calls.append(
            executable
        )

    def connect_window(
        self,
        title,
    ):

        self.connect_calls.append(
            title
        )

        return self.window


class LaunchFailureUIAdapter(
    FakeUIAdapter,
):

    def launch_application(
        self,
        executable,
    ):

        raise RuntimeError(
            "Launch failed."
        )


class ConnectFailureUIAdapter(
    FakeUIAdapter,
):

    def connect_window(
        self,
        title,
    ):

        raise RuntimeError(
            "Connect failed."
        )


# ============================================================
# Helpers
# ============================================================

def make_context(
    ui_adapter,
):

    return RecoveryContext(

        executable="calc.exe",

        window_title="Calculator",

        ui_adapter=ui_adapter,

        replay_engine=Dummy(),

        graph=Dummy(),

        memory=Dummy(),

        root_state_id="ROOT",
    )


# ============================================================
# Tests
# ============================================================

def test_launch_is_called():

    adapter = FakeUIAdapter()

    executor = RecoveryExecutor()

    executor.execute(
        make_context(adapter),
        make_context(adapter),
    )

    assert adapter.launch_calls == [
        "calc.exe"
    ]


def test_connect_is_called():

    adapter = FakeUIAdapter()

    executor = RecoveryExecutor()

    executor.execute(
        make_context(adapter)
    )

    assert adapter.connect_calls == [
        "Calculator"
    ]


def test_success_returns_execution_result():

    adapter = FakeUIAdapter()

    executor = RecoveryExecutor()

    result = executor.execute(
        make_context(adapter)
    )

    assert isinstance(
        result,
        RecoveryExecutionResult,
    )

    assert result.success

    assert (
        result.window
        is adapter.window
    )

    assert result.error_message is None


def test_launch_failure_returns_failed_result():

    adapter = LaunchFailureUIAdapter()

    executor = RecoveryExecutor()

    result = executor.execute(
        make_context(adapter)
    )

    assert not result.success

    assert result.window is None

    assert (
        result.error_message
        ==
        "Launch failed."
    )


def test_connect_failure_returns_failed_result():

    adapter = ConnectFailureUIAdapter()

    executor = RecoveryExecutor()

    result = executor.execute(
        make_context(adapter)
    )

    assert not result.success

    assert result.window is None

    assert (
        result.error_message
        ==
        "Connect failed."
    )


def main():

    print()

    print(
        "===== RECOVERY EXECUTOR TESTS ====="
    )

    print()

    tests = [

        test_launch_is_called,

        test_connect_is_called,

        test_success_returns_execution_result,

        test_launch_failure_returns_failed_result,

        test_connect_failure_returns_failed_result,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RecoveryExecutor tests passed successfully."
    )


if __name__ == "__main__":

    main()