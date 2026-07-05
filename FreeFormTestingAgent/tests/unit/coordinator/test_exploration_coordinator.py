"""
Unit tests for ExplorationCoordinator.

What These Tests Prove:

    1. The coordinator stops when no target remains.

    2. It repeatedly reselects targets after each step.

    3. max_steps limits continuation work.

    4. Failed steps are counted.

    5. max_failures stops the loop.

    6. Successful new states are counted.

The test uses controlled fake components because replay, action
execution, graph updates, and memory updates are already tested by
ExplorationStepExecutor.
"""

from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)

from agent.coordinator.exploration_coordinator import (
    ExplorationCoordinator,
)

from agent.explorer.exploration_step_result import (
    ExplorationStepResult,
)


class FakeTarget:
    """
    Minimal target object required by the coordinator.
    """

    def __init__(
        self,
        state_id,
    ):
        self.state_id = state_id


class FakeTargetSelector:
    """
    Return controlled targets in sequence.

    Each call removes one target.

    After the sequence is exhausted, return None.
    """

    def __init__(
        self,
        state_ids,
    ):
        self.targets = [
            FakeTarget(state_id)
            for state_id in state_ids
        ]

        self.calls = 0

    def select_next_target(
        self,
    ):
        self.calls += 1

        if not self.targets:
            return None

        return self.targets.pop(0)


class FakeStepExecutor:
    """
    Return controlled ExplorationStepResult objects.
    """

    def __init__(
        self,
        results,
    ):
        self.results = list(
            results
        )

        self.calls = []

    def execute_step(
        self,
        root_state_id,
        source_state_id,
    ):
        self.calls.append(
            (
                root_state_id,
                source_state_id,
            )
        )

        return self.results.pop(0)


def successful_result(
    source_state_id,
    new_state=True,
):
    """
    Create a controlled successful step result.
    """

    return ExplorationStepResult(
        source_state_id=source_state_id,
        target_state_id=(
            f"{source_state_id}_target"
        ),
        replay_success=True,
        execution_success=True,
        new_state_discovered=new_state,
    )


def failed_result(
    source_state_id,
):
    """
    Create a controlled failed step result.
    """

    return ExplorationStepResult(
        source_state_id=source_state_id,
        replay_success=False,
        execution_success=False,
        new_state_discovered=False,
        failure_reason="REPLAY_FAILED",
    )


def test_stops_when_no_target_remains():
    """
    Empty target selection must finish without attempting a step.
    """

    selector = FakeTargetSelector(
        []
    )

    executor = FakeStepExecutor(
        []
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,
        step_executor=executor,
        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 0

    assert result.successful_steps == 0

    assert result.failed_steps == 0

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.NO_REMAINING_TARGETS
    )


def test_repeatedly_selects_and_executes_targets():
    """
    The coordinator must return to target selection after every step.
    """

    selector = FakeTargetSelector(
        [
            "S1",
            "S2",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
            successful_result("S2"),
        ]
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,
        step_executor=executor,
        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 2

    assert result.successful_steps == 2

    assert result.failed_steps == 0

    assert selector.calls == 3

    assert executor.calls == [
        ("ROOT", "S1"),
        ("ROOT", "S2"),
    ]

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.NO_REMAINING_TARGETS
    )


def test_max_steps_stops_continuation():
    """
    max_steps must stop the coordinator before another target is selected.
    """

    selector = FakeTargetSelector(
        [
            "S1",
            "S2",
            "S3",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
            successful_result("S2"),
            successful_result("S3"),
        ]
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,
        step_executor=executor,
        limits=CoordinatorLimits(
            max_steps=2,
            max_duration=None,
            max_failures=None,
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 2

    assert len(
        executor.calls
    ) == 2

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.MAX_STEPS_REACHED
    )


def test_failed_steps_are_counted():
    """
    Failed step results must contribute to failed_steps.
    """

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            failed_result("S1"),
        ]
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,
        step_executor=executor,
        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 1

    assert result.successful_steps == 0

    assert result.failed_steps == 1

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.NO_REMAINING_TARGETS
    )


def test_max_failures_stops_continuation():
    """
    Failure budget must stop the loop before selecting more work.
    """

    selector = FakeTargetSelector(
        [
            "S1",
            "S2",
            "S3",
        ]
    )

    executor = FakeStepExecutor(
        [
            failed_result("S1"),
            failed_result("S2"),
            successful_result("S3"),
        ]
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,
        step_executor=executor,
        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=2,
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 2

    assert result.failed_steps == 2

    assert len(
        executor.calls
    ) == 2

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.MAX_FAILURES_REACHED
    )


def test_new_states_are_counted():
    """
    Only successful steps reporting new states should increase new_states.
    """

    selector = FakeTargetSelector(
        [
            "S1",
            "S2",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result(
                "S1",
                new_state=True,
            ),
            successful_result(
                "S2",
                new_state=False,
            ),
        ]
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,
        step_executor=executor,
        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 2

    assert result.successful_steps == 2

    assert result.new_states == 1


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_stops_when_no_target_remains,
        test_repeatedly_selects_and_executes_targets,
        test_max_steps_stops_continuation,
        test_failed_steps_are_counted,
        test_max_failures_stops_continuation,
        test_new_states_are_counted,
    ]

    print()

    print(
        "===== EXPLORATION COORDINATOR TESTS ====="
    )

    print()

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All ExplorationCoordinator tests passed successfully."
    )


if __name__ == "__main__":

    main()