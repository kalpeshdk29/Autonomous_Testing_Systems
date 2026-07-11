"""
File:
    test_calculator_coordinator_runtime_failure.py

Purpose:
    Verify the complete real runtime-failure pipeline:

        Real Calculator
            ↓
        Initial real BFS exploration
            ↓
        Save initial session
            ↓
        Load fresh graph + memory
            ↓
        Capture real Calculator window PID
            ↓
        WindowsProcessHandle
            ↓
        ProcessHealthProbe
            ↓
        ApplicationDisappearedDetector
            ↓
        RuntimeHealthMonitor
            ↓
        ExplorationCoordinator
            ↓
        Pre-step health check → healthy
            ↓
        Controlled step kills exact Calculator PID
            ↓
        Post-step health check → unhealthy
            ↓
        APPLICATION_DISAPPEARED
            ↓
        FailureStore
            ↓
        Automatic CheckpointManager checkpoint
            ↓
        RUNTIME_HEALTH_FAILED
            ↓
        Fresh repository load
            ↓
        APPLICATION_DISAPPEARED restored from disk

Critical Rule:

    After coordinator.run() completes, this test does NOT manually
    save the session.

    Therefore, the persisted runtime failure can exist only because:

        RuntimeHealthMonitor
            ↓
        ExplorationCoordinator
            ↓
        FailureStore
            ↓
        CheckpointManager
            ↓
        JsonSessionRepository

    worked as one complete runtime pipeline.

Important:

    The calc.exe launcher PID is NOT tracked.

    Windows Calculator launches a separate long-lived process.
    Therefore, this test tracks:

        window.ProcessId

    which belongs to the actual Calculator window.
"""

import shutil
import subprocess
import time

from datetime import datetime
from pathlib import Path


from tests.fixtures.calculator_fixture import (
    CalculatorFixture,
)


from adapters.process.windows_process_handle import (
    WindowsProcessHandle,
)


from core.graph.state_graph import (
    StateGraph,
)


from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)

from agent.coordinator.exploration_coordinator import (
    ExplorationCoordinator,
)


from agent.executor.action_executor import (
    ActionExecutor,
)


from agent.explorer.action_filter import (
    ActionFilter,
)

from agent.explorer.bfs_explorer import (
    BFSExplorer,
)

from agent.explorer.exploration_limits import (
    ExplorationLimits,
)

from agent.explorer.exploration_step_result import (
    ExplorationStepResult,
)


from agent.failure.application_disappeared_detector import (
    ApplicationDisappearedDetector,
)

from agent.failure.failure_store import (
    FailureStore,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.failure.process_health_probe import (
    ProcessHealthProbe,
)

from agent.failure.runtime_health_monitor import (
    RuntimeHealthMonitor,
)


from agent.memory.exploration_memory import (
    ExplorationMemory,
)


from agent.persistence.checkpoint_manager import (
    CheckpointManager,
)

from agent.persistence.json_session_repository import (
    JsonSessionRepository,
)

from agent.persistence.session_serializer import (
    SessionSerializer,
)

from agent.persistence.session_snapshot import (
    ExplorationSessionSnapshot,
)

from agent.persistence.session_status import (
    SessionStatus,
)


from agent.replay.replay_engine import (
    ReplayEngine,
)


# =============================================================
# TEST CONFIGURATION
# =============================================================


SESSION_ID = (
    "calculator-coordinator-runtime-failure-integration"
)


STORAGE_ROOT = Path(
    "storage/database/sessions"
)


PROCESS_NAME = (
    "CalculatorApp.exe"
)


# =============================================================
# CONTROLLED CALCULATOR POLICY
# =============================================================


class CalculatorRuntimeFailureActionFilter(
    ActionFilter
):
    """
    Small deterministic Calculator exploration policy.

    Initial exploration exists only to produce:

        - a real root state
        - a real graph
        - real exploration memory

    for the runtime-failure persistence test.
    """

    ALLOWED_ACTIONS = {
        "num7Button",
        "num8Button",
        "plusButton",
        "equalButton",
    }

    def allow(
        self,
        action,
    ) -> bool:

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
        )


# =============================================================
# RECORDING REPOSITORY
# =============================================================


class RecordingJsonSessionRepository:
    """
    Decorator around the real JsonSessionRepository.

    Real filesystem persistence remains active.

    The decorator only counts save calls.

    Expected flow:

        Initial manual save:
            1

        Runtime-failure checkpoint:
            1

        Total:
            2
    """

    def __init__(
        self,
        repository,
    ):

        self.repository = repository

        self.save_calls = 0

    def save(
        self,
        snapshot,
    ):

        self.save_calls += 1

        return self.repository.save(
            snapshot
        )

    def load(
        self,
        session_id,
    ):

        return self.repository.load(
            session_id
        )

    def exists(
        self,
        session_id,
    ):

        return self.repository.exists(
            session_id
        )

    def list_sessions(
        self,
    ):

        return (
            self.repository
            .list_sessions()
        )


# =============================================================
# CONTROLLED COORDINATOR TARGET
# =============================================================


class ControlledRuntimeFailureTarget:
    """
    Minimal exploration target required by the coordinator.
    """

    def __init__(
        self,
        state_id: str,
    ):

        self.state_id = state_id


class OneRuntimeFailureTargetSelector:
    """
    Return exactly one exploration target.

    The coordinator should stop because runtime health fails
    after that step.
    """

    def __init__(
        self,
        state_id: str,
    ):

        self.target = (
            ControlledRuntimeFailureTarget(
                state_id
            )
        )

        self.calls = 0

    def select_next_target(
        self,
    ):

        self.calls += 1

        if self.target is None:

            return None

        target = self.target

        self.target = None

        return target


# =============================================================
# REAL PROCESS FAILURE INJECTION
# =============================================================


class CalculatorKillingStepExecutor:
    """
    Kill the exact Calculator process during one coordinator step.

    Required coordinator flow:

        pre-step runtime check
            ↓
        Calculator healthy
            ↓
        execute_step()
            ↓
        kill exact Calculator PID
            ↓
        return failed step result
            ↓
        post-step runtime check
            ↓
        APPLICATION_DISAPPEARED

    The returned step result is intentionally failed.

    However, the runtime-health failure must take priority over any
    secondary execution-failure classification.
    """

    FAILURE_DURATION = 1.0

    def __init__(
        self,
        process_id: int,
    ):

        self.process_id = (
            process_id
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

        start_time = time.time()

        result = subprocess.run(
            [
                "taskkill",
                "/F",
                "/PID",
                str(
                    self.process_id
                ),
            ],

            capture_output=True,

            text=True,

            check=False,
        )

        if result.returncode != 0:

            raise RuntimeError(
                "Failed to terminate tracked "
                "Calculator process. "
                f"PID={self.process_id}, "
                f"stdout={result.stdout!r}, "
                f"stderr={result.stderr!r}"
            )

        # Give Windows a short opportunity to complete process
        # termination before the coordinator performs its
        # post-step runtime-health check.

        time.sleep(
            0.5
        )

        duration = (
            time.time()
            -
            start_time
        )

        return ExplorationStepResult(
            source_state_id=(
                source_state_id
            ),

            selected_action=None,

            target_state_id=None,

            transition=None,

            replay_success=True,

            execution_success=False,

            new_state_discovered=False,

            duration=duration,

            failure_reason=(
                "ACTION_EXECUTION_FAILED"
            ),
        )


# =============================================================
# HELPERS
# =============================================================

def get_current_calculator_process_id(
    ui,
    timeout: float = 10.0,
) -> int:
    """
    Reconnect to the currently active Calculator window and return
    the PID that owns that fresh window.

    The original fixture window may become stale during BFS replay
    because exploration can relaunch or reconnect to Calculator.
    """

    deadline = (
        time.time()
        +
        timeout
    )

    last_error = None

    while time.time() < deadline:

        try:

            current_window = (
                ui.connect_window(
                    "Calculator"
                )
            )

            process_id = (
                current_window.ProcessId
            )

            if (
                isinstance(
                    process_id,
                    int,
                )
                and
                process_id > 0
            ):

                return process_id

        except Exception as error:

            last_error = error

        time.sleep(
            0.2
        )

    raise RuntimeError(
        "Could not resolve the current "
        "Calculator window process ID "
        f"within {timeout} seconds. "
        f"Last error: {last_error!r}"
    )


def get_transition_count(
    graph: StateGraph,
) -> int:
    """
    Return total graph transitions.
    """

    return sum(
        len(transitions)
        for transitions
        in graph.edges.values()
    )


# =============================================================
# REAL END-TO-END RUNTIME FAILURE TEST
# =============================================================


def test_calculator_coordinator_runtime_failure():
    """
    Verify that a real Calculator process disappearance is:

        - observed from the operating system
        - classified as APPLICATION_DISAPPEARED
        - returned to the coordinator
        - stored in FailureStore
        - automatically checkpointed
        - reconstructed from disk
    """

    real_repository = (
        JsonSessionRepository(
            storage_root=(
                STORAGE_ROOT
            )
        )
    )

    repository = (
        RecordingJsonSessionRepository(
            real_repository
        )
    )

    session_directory = (
        STORAGE_ROOT
        /
        SESSION_ID
    )

    if session_directory.exists():

        shutil.rmtree(
            session_directory
        )

    try:

        with CalculatorFixture() as (
            ui,
            window,
        ):

            # =================================================
            # PHASE A
            # INITIAL REAL CALCULATOR EXPLORATION
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE A: INITIAL REAL EXPLORATION"
            )

            print(
                "======================================"
            )

            initial_graph = (
                StateGraph()
            )

            initial_memory = (
                ExplorationMemory()
            )

            action_filter = (
                CalculatorRuntimeFailureActionFilter()
            )

            initial_executor = (
                ActionExecutor()
            )

            initial_replay_engine = (
                ReplayEngine(
                    ui,
                    initial_executor,
                    initial_graph,
                )
            )

            initial_explorer = (
                BFSExplorer(
                    ui=ui,

                    executor=(
                        initial_executor
                    ),

                    graph=(
                        initial_graph
                    ),

                    memory=(
                        initial_memory
                    ),

                    replay_engine=(
                        initial_replay_engine
                    ),

                    executable=(
                        "calc.exe"
                    ),

                    window_title=(
                        "Calculator"
                    ),

                    action_filter=(
                        action_filter
                    ),

                    limits=(
                        ExplorationLimits(
                            max_states=20,

                            max_actions=12,

                            max_transitions=20,

                            max_depth=2,

                            max_duration=120.0,

                            max_failures=10,
                        )
                    ),
                )
            )

            initial_result = (
                initial_explorer
                .explore(
                    window
                )
            )

            print()

            print(
                "===== INITIAL EXPLORATION RESULT ====="
            )

            print(
                initial_result
            )

            root_state_id = (
                initial_result
                .root_state_id
            )

            assert (
                root_state_id
                is not None
            )

            assert (
                initial_graph
                .get_state(
                    root_state_id
                )
                is not None
            )

            initial_state_count = len(
                initial_graph.states
            )

            initial_transition_count = (
                get_transition_count(
                    initial_graph
                )
            )

            print()

            print(
                "Initial States:",
                initial_state_count,
            )

            print(
                "Initial Transitions:",
                initial_transition_count,
            )

            # =================================================
            # PHASE B
            # CAPTURE REAL WINDOW-OWNING PROCESS ID
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE B: CAPTURE REAL APPLICATION PID"
            )

            print(
                "======================================"
            )

            tracked_process_id = (
                get_current_calculator_process_id(
                    ui=ui,
            )
)

            assert (
                tracked_process_id
                >
                0
            )

            print(
                "Tracked Calculator PID:",
                tracked_process_id,
            )

            # =================================================
            # PHASE C
            # SAVE INITIAL CLEAN SESSION
            #
            # This is the only manual save in the test.
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE C: SAVE INITIAL SESSION"
            )

            print(
                "======================================"
            )

            created_at = (
                datetime.now()
            )

            initial_snapshot = (
                ExplorationSessionSnapshot(
                    schema_version=(
                        SessionSerializer
                        .CURRENT_SCHEMA_VERSION
                    ),

                    session_id=(
                        SESSION_ID
                    ),

                    root_state_id=(
                        root_state_id
                    ),

                    status=(
                        SessionStatus.CREATED
                    ),

                    created_at=(
                        created_at
                    ),

                    updated_at=(
                        created_at
                    ),

                    graph=(
                        initial_graph
                    ),

                    memory=(
                        initial_memory
                    ),

                    failures=[],
                )
            )

            initial_saved_path = (
                repository.save(
                    initial_snapshot
                )
            )

            assert (
                initial_saved_path
                .is_file()
            )

            assert (
                repository.save_calls
                ==
                1
            )

            print(
                "Initial Session Saved:",
                initial_saved_path,
            )

            # =================================================
            # PHASE D
            # LOAD FRESH SESSION OBJECTS
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE D: LOAD FRESH SESSION"
            )

            print(
                "======================================"
            )

            loaded_snapshot = (
                repository.load(
                    SESSION_ID
                )
            )

            resumed_graph = (
                loaded_snapshot.graph
            )

            resumed_memory = (
                loaded_snapshot.memory
            )

            assert (
                resumed_graph
                is not
                initial_graph
            )

            assert (
                resumed_memory
                is not
                initial_memory
            )

            assert (
                loaded_snapshot.failures
                ==
                []
            )

            assert (
                loaded_snapshot
                .root_state_id
                ==
                root_state_id
            )

            assert (
                len(
                    resumed_graph.states
                )
                ==
                initial_state_count
            )

            assert (
                get_transition_count(
                    resumed_graph
                )
                ==
                initial_transition_count
            )

            # =================================================
            # PHASE E
            # BUILD REAL RUNTIME HEALTH PIPELINE
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE E: BUILD RUNTIME HEALTH PIPELINE"
            )

            print(
                "======================================"
            )

            process_handle = (
                WindowsProcessHandle(
                    process_id=(
                        tracked_process_id
                    )
                )
            )

            process_probe = (
                ProcessHealthProbe(
                    process_name=(
                        PROCESS_NAME
                    ),

                    process=(
                        process_handle
                    ),
                )
            )

            application_detector = (
                ApplicationDisappearedDetector()
            )

            runtime_health_monitor = (
                RuntimeHealthMonitor(
                    probe=(
                        process_probe
                    ),

                    detector=(
                        application_detector
                    ),
                )
            )

            # Verify the runtime is healthy before handing control
            # to the coordinator.

            initial_health_failure = (
                runtime_health_monitor
                .check(
                    source_state_id=(
                        root_state_id
                    )
                )
            )

            assert (
                initial_health_failure
                is None
            )

            print(
                "Initial Runtime Health:",
                "HEALTHY",
            )

            # =================================================
            # PHASE F
            # BUILD DURABLE COORDINATOR RUNTIME
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE F: BUILD COORDINATOR RUNTIME"
            )

            print(
                "======================================"
            )

            failure_store = (
                FailureStore()
            )

            target_selector = (
                OneRuntimeFailureTargetSelector(
                    state_id=(
                        root_state_id
                    )
                )
            )

            step_executor = (
                CalculatorKillingStepExecutor(
                    process_id=(
                        tracked_process_id
                    )
                )
            )

            checkpoint_manager = (
                CheckpointManager(
                    session_id=(
                        SESSION_ID
                    ),

                    root_state_id=(
                        loaded_snapshot
                        .root_state_id
                    ),

                    graph=(
                        resumed_graph
                    ),

                    memory=(
                        resumed_memory
                    ),

                    repository=(
                        repository
                    ),

                    created_at=(
                        loaded_snapshot
                        .created_at
                    ),

                    status=(
                        SessionStatus.RUNNING
                    ),

                    failure_store=(
                        failure_store
                    ),
                )
            )

            coordinator = (
                ExplorationCoordinator(
                    target_selector=(
                        target_selector
                    ),

                    step_executor=(
                        step_executor
                    ),

                    limits=(
                        CoordinatorLimits(
                            max_steps=5,

                            max_duration=120.0,

                            max_failures=5,
                        )
                    ),

                    checkpoint_manager=(
                        checkpoint_manager
                    ),

                    failure_store=(
                        failure_store
                    ),

                    runtime_health_monitor=(
                        runtime_health_monitor
                    ),
                )
            )

            # =================================================
            # PHASE G
            # RUN COORDINATOR
            #
            # Required order:
            #
            #     pre-step health → healthy
            #         ↓
            #     execute step
            #         ↓
            #     kill exact Calculator PID
            #         ↓
            #     post-step health → unhealthy
            #         ↓
            #     APPLICATION_DISAPPEARED
            #         ↓
            #     FailureStore
            #         ↓
            #     automatic checkpoint
            #         ↓
            #     RUNTIME_HEALTH_FAILED
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE G: RUN COORDINATOR"
            )

            print(
                "======================================"
            )

            coordinator_result = (
                coordinator.run(
                    root_state_id=(
                        loaded_snapshot
                        .root_state_id
                    )
                )
            )

            print()

            print(
                "===== COORDINATOR RESULT ====="
            )

            print(
                "Steps:",
                coordinator_result.steps,
            )

            print(
                "Successful Steps:",
                coordinator_result
                .successful_steps,
            )

            print(
                "Failed Steps:",
                coordinator_result
                .failed_steps,
            )

            print(
                "Structured Failures:",
                len(
                    coordinator_result
                    .failures
                ),
            )

            print(
                "Stop Reason:",
                coordinator_result
                .stop_reason,
            )

            # =================================================
            # VERIFY COORDINATOR RESULT
            # =================================================

            assert (
                coordinator_result.steps
                ==
                1
            )

            assert (
                coordinator_result
                .successful_steps
                ==
                0
            )

            assert (
                coordinator_result
                .failed_steps
                ==
                1
            )

            assert (
                coordinator_result
                .stop_reason
                ==
                CoordinatorStopReason
                .RUNTIME_HEALTH_FAILED
            )

            assert (
                len(
                    coordinator_result
                    .failures
                )
                ==
                1
            )

            # =================================================
            # VERIFY LIVE RUNTIME FAILURE
            # =================================================

            assert (
                failure_store.count
                ==
                1
            )

            live_failure = (
                failure_store
                .failures[0]
            )

            assert (
                live_failure
                is
                coordinator_result
                .failures[0]
            )

            assert (
                live_failure
                .failure_type
                ==
                FailureType
                .APPLICATION_DISAPPEARED
            )

            assert (
                live_failure
                .source_state_id
                ==
                root_state_id
            )

            assert (
                live_failure
                .metadata[
                    "process_name"
                ]
                ==
                PROCESS_NAME
            )

            assert (
                live_failure
                .metadata[
                    "process_id"
                ]
                ==
                tracked_process_id
            )

            assert (
                live_failure
                .metadata[
                    "is_running"
                ]
                is False
            )

            assert (
                live_failure
                .recoverable
            )

            live_failure_id = (
                live_failure
                .failure_id
            )

            live_failure_timestamp = (
                live_failure
                .timestamp
            )

            live_failure_message = (
                live_failure
                .message
            )

            live_failure_metadata = dict(
                live_failure.metadata
            )

            print()

            print(
                "===== LIVE RUNTIME FAILURE ====="
            )

            print(
                "Failure ID:",
                live_failure_id,
            )

            print(
                "Failure Type:",
                live_failure
                .failure_type,
            )

            print(
                "Source State:",
                live_failure
                .source_state_id,
            )

            print(
                "Recoverable:",
                live_failure
                .recoverable,
            )

            print(
                "Metadata:",
                live_failure_metadata,
            )

            # =================================================
            # VERIFY AUTOMATIC CHECKPOINT COUNT
            #
            # Save 1:
            #     initial manual session
            #
            # Save 2:
            #     runtime-failure checkpoint
            # =================================================

            assert (
                repository.save_calls
                ==
                2
            ), (
                "Expected one initial manual save "
                "and one automatic runtime-failure "
                "checkpoint."
            )

            assert (
                checkpoint_manager
                .last_checkpoint_at
                is not None
            )

            # =================================================
            # CRITICAL TEST BOUNDARY
            #
            # DO NOT CALL:
            #
            #     repository.save(...)
            #
            # The runtime failure must already exist on disk.
            # =================================================

            # =================================================
            # PHASE H
            # LOAD SESSION DIRECTLY FROM DISK
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE H: LOAD RUNTIME FAILURE FROM DISK"
            )

            print(
                "======================================"
            )

            final_snapshot = (
                real_repository.load(
                    SESSION_ID
                )
            )

            # =================================================
            # VERIFY FRESH RECONSTRUCTION
            # =================================================

            assert (
                final_snapshot.graph
                is not
                resumed_graph
            )

            assert (
                final_snapshot.memory
                is not
                resumed_memory
            )

            assert (
                final_snapshot.failures
                is not
                failure_store.failures
            )

            # =================================================
            # VERIFY SESSION METADATA
            # =================================================

            assert (
                final_snapshot
                .session_id
                ==
                SESSION_ID
            )

            assert (
                final_snapshot
                .root_state_id
                ==
                root_state_id
            )

            assert (
                final_snapshot
                .created_at
                ==
                created_at
            )

            assert (
                final_snapshot
                .updated_at
                ==
                checkpoint_manager
                .last_checkpoint_at
            )

            assert (
                final_snapshot
                .status
                ==
                SessionStatus.RUNNING
            )

            # =================================================
            # VERIFY RUNTIME FAILURE SURVIVED DISK ROUND-TRIP
            # =================================================

            assert (
                len(
                    final_snapshot
                    .failures
                )
                ==
                1
            )

            disk_failure = (
                final_snapshot
                .failures[0]
            )

            # Fresh reconstructed object.

            assert (
                disk_failure
                is not
                live_failure
            )

            # Stable identity survived.

            assert (
                disk_failure
                .failure_id
                ==
                live_failure_id
            )

            # Runtime failure type survived.

            assert (
                disk_failure
                .failure_type
                ==
                FailureType
                .APPLICATION_DISAPPEARED
            )

            assert isinstance(
                disk_failure
                .failure_type,

                FailureType,
            )

            # Source context survived.

            assert (
                disk_failure
                .source_state_id
                ==
                root_state_id
            )

            # Description survived.

            assert (
                disk_failure
                .message
                ==
                live_failure_message
            )

            # Timestamp survived.

            assert (
                disk_failure
                .timestamp
                ==
                live_failure_timestamp
            )

            # Process metadata survived.

            assert (
                disk_failure
                .metadata
                ==
                live_failure_metadata
            )

            assert (
                disk_failure
                .metadata[
                    "process_id"
                ]
                ==
                tracked_process_id
            )

            assert (
                disk_failure
                .metadata[
                    "process_name"
                ]
                ==
                PROCESS_NAME
            )

            assert (
                disk_failure
                .metadata[
                    "is_running"
                ]
                is False
            )

            assert (
                disk_failure
                .recoverable
            )

            # Runtime process failure did not represent a graph
            # action or transition.

            assert (
                disk_failure.action
                is None
            )

            assert (
                disk_failure
                .target_state_id
                is None
            )

            # =================================================
            # VERIFY GRAPH AND MEMORY WERE NOT CORRUPTED
            # =================================================

            assert (
                len(
                    final_snapshot
                    .graph
                    .states
                )
                ==
                len(
                    resumed_graph
                    .states
                )
            )

            assert (
                get_transition_count(
                    final_snapshot.graph
                )
                ==
                get_transition_count(
                    resumed_graph
                )
            )

            # =================================================
            # FINAL RESULT
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "DURABLE RUNTIME FAILURE VERIFIED"
            )

            print(
                "======================================"
            )

            print(
                "Tracked Application PID:",
                tracked_process_id,
            )

            print(
                "Coordinator Steps:",
                coordinator_result.steps,
            )

            print(
                "Failed Steps:",
                coordinator_result
                .failed_steps,
            )

            print(
                "Stop Reason:",
                coordinator_result
                .stop_reason,
            )

            print(
                "Live Failure Count:",
                failure_store.count,
            )

            print(
                "Disk Failure Count:",
                len(
                    final_snapshot
                    .failures
                ),
            )

            print(
                "Failure Type:",
                disk_failure
                .failure_type,
            )

            print(
                "Failure ID Preserved:",
                (
                    disk_failure
                    .failure_id
                    ==
                    live_failure_id
                ),
            )

            print(
                "Process ID Preserved:",
                (
                    disk_failure
                    .metadata[
                        "process_id"
                    ]
                    ==
                    tracked_process_id
                ),
            )

            print(
                "Initial Manual Saves:",
                1,
            )

            print(
                "Automatic Runtime Failure Checkpoints:",
                1,
            )

            print(
                "Total Repository Saves:",
                repository.save_calls,
            )

            print(
                "Disk Matches Live Runtime Failure:",
                (
                    disk_failure.failure_id
                    ==
                    live_failure.failure_id

                    and

                    disk_failure.failure_type
                    ==
                    live_failure.failure_type

                    and

                    disk_failure.metadata
                    ==
                    live_failure.metadata
                ),
            )

            print()

            print(
                "CALCULATOR COORDINATOR RUNTIME "
                "FAILURE TEST PASSED"
            )

    finally:

        if session_directory.exists():

            shutil.rmtree(
                session_directory
            )


if __name__ == "__main__":

    test_calculator_coordinator_runtime_failure()