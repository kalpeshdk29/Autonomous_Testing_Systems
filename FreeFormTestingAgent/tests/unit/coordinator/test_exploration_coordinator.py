"""
Unit tests for ExplorationCoordinator.

What These Tests Prove:

    1. The coordinator stops when no target remains.

    2. It repeatedly reselects targets after each step.

    3. max_steps limits continuation work.

    4. Failed steps are counted.

    5. max_failures stops the loop.

    6. Successful new states are counted.

    7. Checkpoint persistence remains optional.

    8. Successful and failed steps trigger checkpoints.

    9. Checkpoint failure stops continuation.

    10. Structured failure detection remains optional.

    11. Recognized failures are stored.

    12. Successful steps create no failure record.

    13. Unsupported failed outcomes create no failure record.

    14. CoordinatorResult contains current-run failure history.
"""

from unittest import result

from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.failure.failure_record import (
    FailureRecord,
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

from agent.failure.execution_failure_detector import (
    ExecutionFailureDetector,
)

from agent.failure.failure_store import (
    FailureStore,
)

from agent.failure.failure_type import (
    FailureType,
)


# =============================================================
# FAKES
# =============================================================


class FakeTarget:
    """
    Minimal target object required by the coordinator.
    """

    def __init__(
        self,
        state_id,
    ):

        self.state_id = state_id


class FakeRecoveryManager:

    def __init__(
        self,
        success=True,
    ):

        self.success = success

        self.calls = 0

        self.failure = None

        self.context = None

    def recover(
        self,
        failure,
        context,
    ):

        from agent.recovery.recovery_result import (
            RecoveryResult,
        )

        self.calls += 1

        self.failure = failure

        self.context = context

        return RecoveryResult(
            success=self.success,
            recovered_state_id=None,
            duration=0,
        )

class FakeRecoveryContext:
    pass


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
            FakeTarget(
                state_id
            )
            for state_id
            in state_ids
        ]

        self.calls = 0

    def select_next_target(
        self,
    ):

        self.calls += 1

        if not self.targets:

            return None

        return self.targets.pop(
            0
        )


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

        return self.results.pop(
            0
        )

class FakeRuntimeHealthMonitor:
    """
    Return controlled runtime-health results.

    Each check removes and returns one result.

    A result may be:

        None
            → runtime is healthy

        FailureRecord
            → runtime health failed
    """

    def __init__(
        self,
        results,
    ):

        self.results = list(
            results
        )

        self.calls = []

    def check(
        self,
        source_state_id,
    ):

        self.calls.append(
            source_state_id
        )

        if not self.results:

            return None

        return self.results.pop(0)

class FakeFailureDetector:
    """
    Return controlled execution-failure detection results.
    """

    def __init__(
        self,
        results,
    ):

        self.results = list(
            results
        )

        self.calls = []

    def detect(
        self,
        step_result,
    ):

        self.calls.append(
            step_result
        )

        if not self.results:

            return None

        return self.results.pop(0)


class RecordingCheckpointManager:
    """
    Record successful checkpoint calls.
    """

    def __init__(
        self,
    ):

        self.calls = 0

    def checkpoint(
        self,
    ):

        self.calls += 1


class FailingCheckpointManager:
    """
    Fail on every checkpoint attempt.
    """

    def __init__(
        self,
    ):

        self.calls = 0

    def checkpoint(
        self,
    ):

        self.calls += 1

        raise RuntimeError(
            "Simulated checkpoint failure."
        )


# =============================================================
# RESULT HELPERS
# =============================================================

def make_failure(
    source_state_id: str = "S1",
):
    """
    Create a deterministic structured failure for coordinator tests.
    """

    return FailureRecord(
        failure_type=(
            FailureType
            .APPLICATION_DISAPPEARED
        ),

        message=(
            "Application disappeared."
        ),

        source_state_id=(
            source_state_id
        ),

        action=None,

        target_state_id=None,

        replay_path=[],

        screenshot_path=None,

        recoverable=True,

        metadata={
            "process_name": (
                "CalculatorApp.exe"
            ),

            "process_id": 1234,
        },
    )


def successful_result(
    source_state_id,
    new_state=True,
):
    """
    Create a controlled successful step result.
    """

    return ExplorationStepResult(
        source_state_id=(
            source_state_id
        ),

        target_state_id=(
            f"{source_state_id}_target"
        ),

        replay_success=True,

        execution_success=True,

        new_state_discovered=(
            new_state
        ),
    )


def failed_result(
    source_state_id,
):
    """
    Create a controlled replay-failure result.
    """

    return ExplorationStepResult(
        source_state_id=(
            source_state_id
        ),

        replay_success=False,

        execution_success=False,

        new_state_discovered=False,

        failure_reason=(
            "REPLAY_FAILED"
        ),
    )

class RecordingFailureStore:
    """
    Test double that records failure records added by the
    exploration coordinator.
    """

    def __init__(self):
        self.failures = []

    def add(self, failure):
        self.failures.append(failure)

def unsupported_failed_result(
    source_state_id,
):
    """
    Create a failed step not recognized by the current execution
    failure detector.
    """

    return ExplorationStepResult(
        source_state_id=(
            source_state_id
        ),

        replay_success=False,

        execution_success=False,

        new_state_discovered=False,

        failure_reason=(
            "SOURCE_STATE_NOT_FOUND"
        ),
    )


# =============================================================
# ORIGINAL COORDINATOR TESTS
# =============================================================


def test_stops_when_no_target_remains():

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

    assert (
        result.successful_steps
        ==
        0
    )

    assert result.failed_steps == 0

    assert result.failures == []

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .NO_REMAINING_TARGETS
    )


def test_pre_step_runtime_failure_recovers_and_continues():
    """
    A successful recovery before execution should allow
    exploration to continue.
    """

    runtime_failure = make_failure(
        source_state_id="S1"
    )

    monitor = FakeRuntimeHealthMonitor(
        [
            runtime_failure,
            None,
            None,
        ]
    )

    recovery_manager = FakeRecoveryManager(
        success=True,
    )

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
        ]
    )

    failure_store = RecordingFailureStore()

    coordinator = ExplorationCoordinator(

        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),

        failure_store=failure_store,

        runtime_health_monitor=monitor,

        recovery_manager=recovery_manager,

        recovery_context=FakeRecoveryContext(),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert recovery_manager.calls == 1

    assert len(executor.calls) == 1

    assert result.steps == 1

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.NO_REMAINING_TARGETS
    )


def test_pre_step_runtime_failed_recovery_stops():
    """
    If recovery fails before execution,
    the coordinator must stop.
    """

    runtime_failure = make_failure(
        source_state_id="S1"
    )

    monitor = FakeRuntimeHealthMonitor(
        [
            runtime_failure,
        ]
    )

    recovery_manager = FakeRecoveryManager(
        success=False,
    )

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
        ]
    )

    failure_store = RecordingFailureStore()

    coordinator = ExplorationCoordinator(

        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),

        failure_store=failure_store,

        runtime_health_monitor=monitor,

        recovery_manager=recovery_manager,

        recovery_context=FakeRecoveryContext(),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert recovery_manager.calls == 1

    assert len(executor.calls) == 0

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason.RECOVERY_FAILED
    )


def test_recovery_manager_receives_failure_and_context():
    """
    Coordinator forwards the detected runtime failure
    and recovery context to the recovery manager.
    """

    runtime_failure = make_failure(
        source_state_id="S1"
    )

    monitor = FakeRuntimeHealthMonitor(
        [
            runtime_failure,
        ]
    )

    recovery_context = FakeRecoveryContext()

    recovery_manager = FakeRecoveryManager(
        success=False,
    )

    failure_store = RecordingFailureStore()

    coordinator = ExplorationCoordinator(

        target_selector=FakeTargetSelector(
            ["S1"]
        ),

        step_executor=FakeStepExecutor(
            [
                successful_result("S1"),
            ]
        ),

        limits=CoordinatorLimits(
            max_steps=10,
            max_duration=None,
            max_failures=5,
        ),

        failure_store=failure_store,

        runtime_health_monitor=monitor,

        recovery_manager=recovery_manager,

        recovery_context=recovery_context,
    )

    coordinator.run(
        root_state_id="ROOT"
    )

    assert (
        recovery_manager.failure
        is runtime_failure
    )

    assert (
        recovery_manager.context
        is recovery_context
    )

def test_repeatedly_selects_and_executes_targets():

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

    assert (
        result.successful_steps
        ==
        2
    )

    assert result.failed_steps == 0

    assert selector.calls == 3

    assert executor.calls == [
        ("ROOT", "S1"),

        ("ROOT", "S2"),
    ]

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .NO_REMAINING_TARGETS
    )


def test_max_steps_stops_continuation():

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
        CoordinatorStopReason
        .MAX_STEPS_REACHED
    )


def test_failed_steps_are_counted():

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

    assert (
        result.successful_steps
        ==
        0
    )

    assert result.failed_steps == 1

    assert result.failures == []

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .NO_REMAINING_TARGETS
    )


def test_max_failures_stops_continuation():

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
        CoordinatorStopReason
        .MAX_FAILURES_REACHED
    )


def test_new_states_are_counted():

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

    assert (
        result.successful_steps
        ==
        2
    )

    assert result.new_states == 1


# =============================================================
# CHECKPOINT TESTS
# =============================================================


def test_coordinator_works_without_checkpoint_manager():

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
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

    assert (
        result.successful_steps
        ==
        1
    )

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .NO_REMAINING_TARGETS
    )


def test_successful_steps_trigger_checkpoints():

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

    checkpoint_manager = (
        RecordingCheckpointManager()
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        checkpoint_manager=(
            checkpoint_manager
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 2

    assert (
        result.successful_steps
        ==
        2
    )

    assert (
        checkpoint_manager.calls
        ==
        2
    )


def test_failed_steps_also_trigger_checkpoints():

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

    checkpoint_manager = (
        RecordingCheckpointManager()
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        checkpoint_manager=(
            checkpoint_manager
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 1

    assert result.failed_steps == 1

    assert (
        checkpoint_manager.calls
        ==
        1
    )


def test_checkpoint_failure_stops_coordinator():

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

    checkpoint_manager = (
        FailingCheckpointManager()
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        checkpoint_manager=(
            checkpoint_manager
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 1

    assert (
        result.successful_steps
        ==
        1
    )

    assert len(
        executor.calls
    ) == 1

    assert (
        checkpoint_manager.calls
        ==
        1
    )

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .CHECKPOINT_FAILED
    )


# =============================================================
# FAILURE DETECTION INTEGRATION TESTS
# =============================================================


def test_coordinator_works_without_failure_detection():

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

    assert result.failed_steps == 1

    assert result.failures == []


def test_detected_failure_is_stored():

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

    failure_detector = (
        ExecutionFailureDetector()
    )

    failure_store = FailureStore()

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        failure_detector=(
            failure_detector
        ),

        failure_store=(
            failure_store
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.failed_steps == 1

    assert failure_store.count == 1

    assert len(
        result.failures
    ) == 1

    failure = result.failures[0]

    assert (
        failure.failure_type
        ==
        FailureType.REPLAY_FAILED
    )

    assert (
        failure.source_state_id
        ==
        "S1"
    )

    assert (
        failure_store.failures[0]
        is
        failure
    )


def test_successful_step_creates_no_failure():

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
        ]
    )

    failure_store = FailureStore()

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        failure_detector=(
            ExecutionFailureDetector()
        ),

        failure_store=(
            failure_store
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert (
        result.successful_steps
        ==
        1
    )

    assert failure_store.count == 0

    assert result.failures == []


def test_unsupported_failed_step_creates_no_failure():

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            unsupported_failed_result(
                "S1"
            ),
        ]
    )

    failure_store = FailureStore()

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        failure_detector=(
            ExecutionFailureDetector()
        ),

        failure_store=(
            failure_store
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.failed_steps == 1

    assert failure_store.count == 0

    assert result.failures == []


def test_multiple_detected_failures_preserve_order():

    selector = FakeTargetSelector(
        [
            "S1",
            "S2",
        ]
    )

    executor = FakeStepExecutor(
        [
            failed_result("S1"),

            failed_result("S2"),
        ]
    )

    failure_store = FailureStore()

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        failure_detector=(
            ExecutionFailureDetector()
        ),

        failure_store=(
            failure_store
        ),
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.failed_steps == 2

    assert failure_store.count == 2

    assert len(
        result.failures
    ) == 2

    assert (
        result.failures[0]
        .source_state_id
        ==
        "S1"
    )

    assert (
        result.failures[1]
        .source_state_id
        ==
        "S2"
    )


def test_detector_requires_failure_store():

    try:

        ExplorationCoordinator(
            target_selector=(
                FakeTargetSelector([])
            ),

            step_executor=(
                FakeStepExecutor([])
            ),

            failure_detector=(
                ExecutionFailureDetector()
            ),
        )

        assert False, (
            "Expected missing failure store "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "failure_store"
            in
            str(error)
        )


def test_failure_store_requires_detector():

    try:

        ExplorationCoordinator(
            target_selector=(
                FakeTargetSelector([])
            ),

            step_executor=(
                FakeStepExecutor([])
            ),

            failure_store=(
                FailureStore()
            ),
        )

        assert False, (
            "Expected missing failure detector "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "failure_detector"
            in
            str(error)
        )

def test_coordinator_works_without_runtime_health_monitor():
    """
    Runtime-health monitoring must remain optional.

    Existing coordinator behavior must continue unchanged.
    """

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
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

    assert result.successful_steps == 1

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .NO_REMAINING_TARGETS
    )


def test_pre_step_runtime_failure_stops_before_execution():
    """
    An unhealthy runtime detected before a step must prevent the
    step from executing.
    """

    runtime_failure = make_failure(
        source_state_id="S1"
    )

    monitor = FakeRuntimeHealthMonitor(
        [
            runtime_failure,
        ]
    )

    selector = FakeTargetSelector(
        [
            "S1",
            "S2",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
        ]
    )

    failure_store = RecordingFailureStore()

    checkpoint_manager = (
        RecordingCheckpointManager()
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        checkpoint_manager=(
            checkpoint_manager
        ),

        failure_store=failure_store,

        runtime_health_monitor=monitor,
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 0

    assert len(
        executor.calls
    ) == 0

    assert (
        monitor.calls
        ==
        [
            "S1",
        ]
    )

    assert (
        failure_store.failures
        ==
        [
            runtime_failure,
        ]
    )

    assert (
        result.failures
        ==
        [
            runtime_failure,
        ]
    )

    assert (
        checkpoint_manager.calls
        ==
        1
    )


    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .RECOVERY_FAILED
    )


def test_post_step_runtime_failure_stops_after_execution():
    """
    A runtime failure detected after execution must stop the
    coordinator after the completed step is recorded.
    """

    runtime_failure = make_failure(
        source_state_id="S1"
    )

    monitor = FakeRuntimeHealthMonitor(
        [
            None,
            runtime_failure,
        ]
    )

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

    failure_store = RecordingFailureStore()

    checkpoint_manager = (
        RecordingCheckpointManager()
    )

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        checkpoint_manager=(
            checkpoint_manager
        ),

        failure_store=failure_store,

        runtime_health_monitor=monitor,
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 1

    assert result.successful_steps == 1

    assert len(
        executor.calls
    ) == 1

    assert (
        monitor.calls
        ==
        [
            "S1",
            "S1",
        ]
    )

    assert (
        failure_store.failures
        ==
        [
            runtime_failure,
        ]
    )

    assert (
        result.failures
        ==
        [
            runtime_failure,
        ]
    )

    assert (
        checkpoint_manager.calls
        ==
        1
    )


    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .RECOVERY_FAILED
    )


def test_healthy_runtime_checks_before_and_after_step():
    """
    A healthy runtime must be checked once before and once after
    each executed exploration step.
    """

    monitor = FakeRuntimeHealthMonitor(
        [
            None,
            None,
        ]
    )

    selector = FakeTargetSelector(
        [
            "S1",
        ]
    )

    executor = FakeStepExecutor(
        [
            successful_result("S1"),
        ]
    )

    failure_store = RecordingFailureStore()

    coordinator = ExplorationCoordinator(
        target_selector=selector,

        step_executor=executor,

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        failure_store=failure_store,

        runtime_health_monitor=monitor,
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 1

    assert (
        monitor.calls
        ==
        [
            "S1",
            "S1",
        ]
    )

    assert (
        failure_store.failures
        ==
        []
    )

    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .NO_REMAINING_TARGETS
    )


def test_post_step_runtime_failure_takes_priority_over_execution_failure():
    """
    If the application disappears during a failed step, the
    runtime failure must be recorded instead of the secondary
    execution failure.
    """

    runtime_failure = make_failure(
        source_state_id="S1"
    )

    monitor = FakeRuntimeHealthMonitor(
        [
            None,
            runtime_failure,
        ]
    )

    detector = FakeFailureDetector(
        [
            make_failure(
                source_state_id="S1"
            ),
        ]
    )

    failure_store = RecordingFailureStore()

    coordinator = ExplorationCoordinator(
        target_selector=(
            FakeTargetSelector(
                [
                    "S1",
                ]
            )
        ),

        step_executor=(
            FakeStepExecutor(
                [
                    failed_result("S1"),
                ]
            )
        ),

        limits=CoordinatorLimits(
            max_steps=10,

            max_duration=None,

            max_failures=5,
        ),

        failure_detector=detector,

        failure_store=failure_store,

        runtime_health_monitor=monitor,
    )

    result = coordinator.run(
        root_state_id="ROOT"
    )

    assert result.steps == 1

    assert (
        failure_store.failures
        ==
        [
            runtime_failure,
        ]
    )

    assert (
        result.failures
        ==
        [
            runtime_failure,
        ]
    )

    assert len(
        detector.calls
    ) == 0


    assert (
        result.stop_reason
        ==
        CoordinatorStopReason
        .RECOVERY_FAILED
    )


def test_runtime_health_monitor_requires_failure_store():
    """
    Runtime failures must have somewhere durable to be stored.
    """

    try:

        ExplorationCoordinator(
            target_selector=(
                FakeTargetSelector([])
            ),

            step_executor=(
                FakeStepExecutor([])
            ),

            runtime_health_monitor=(
                FakeRuntimeHealthMonitor([])
            ),
        )

        assert False, (
            "Expected runtime health monitor "
            "without failure store to be rejected."
        )

    except ValueError as error:

        assert (
            "failure_store"
            in
            str(error)
        )


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


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

        test_coordinator_works_without_checkpoint_manager,

        test_successful_steps_trigger_checkpoints,

        test_failed_steps_also_trigger_checkpoints,

        test_checkpoint_failure_stops_coordinator,

        test_coordinator_works_without_failure_detection,

        test_detected_failure_is_stored,

        test_successful_step_creates_no_failure,

        test_unsupported_failed_step_creates_no_failure,

        test_multiple_detected_failures_preserve_order,

        test_detector_requires_failure_store,

        test_failure_store_requires_detector,
        test_coordinator_works_without_runtime_health_monitor,
        test_pre_step_runtime_failure_stops_before_execution,
        test_post_step_runtime_failure_stops_after_execution,
        test_healthy_runtime_checks_before_and_after_step,
        test_post_step_runtime_failure_takes_priority_over_execution_failure,
        test_runtime_health_monitor_requires_failure_store,

        test_pre_step_runtime_failure_recovers_and_continues,

        test_pre_step_runtime_failed_recovery_stops,

        test_recovery_manager_receives_failure_and_context,
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
        "All ExplorationCoordinator tests "
        "passed successfully."
    )


if __name__ == "__main__":

    main()