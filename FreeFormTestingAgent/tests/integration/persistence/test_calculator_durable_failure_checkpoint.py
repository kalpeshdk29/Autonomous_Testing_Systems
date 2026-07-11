"""
File:
    test_calculator_durable_failure_checkpoint.py

Purpose:
    Verify that a structured failure discovered during a
    coordinator run survives:

        - FailureDetector classification
        - FailureStore storage
        - automatic CheckpointManager persistence
        - JsonSessionRepository disk storage
        - fresh session deserialization

Complete Flow:

    Real Calculator
        ↓
    Initial Real BFS Exploration
        ↓
    Save Initial Session
        ↓
    Load Fresh Graph + Memory
        ↓
    Build Real FailureStore
        ↓
    Build Real CheckpointManager
        ↓
    ExplorationCoordinator
        ↓
    Controlled Failed Step
        ↓
    ExecutionFailureDetector
        ↓
    FailureRecord
        ↓
    FailureStore
        ↓
    Automatic Checkpoint
        ↓
    session.json
        ↓
    Fresh Repository Load
        ↓
    Reconstructed FailureRecord

Critical Rule:

    After coordinator.run() completes, this test does NOT manually
    save the session.

    Therefore, the persisted failure can exist only because:

        Coordinator
            ↓
        FailureDetector
            ↓
        FailureStore
            ↓
        CheckpointManager
            ↓
        JsonSessionRepository

    worked as one complete runtime pipeline.

Important Scope:

    This test does not kill Calculator or destroy its window.

    Application process/window failure detection belongs to the
    next milestone.

    The failed step is controlled so this test isolates durable
    failure persistence.
"""

import shutil

from datetime import datetime
from pathlib import Path


from tests.fixtures.calculator_fixture import (
    CalculatorFixture,
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


from agent.failure.execution_failure_detector import (
    ExecutionFailureDetector,
)

from agent.failure.failure_store import (
    FailureStore,
)

from agent.failure.failure_type import (
    FailureType,
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


SESSION_ID = "calculator-durable-failure-checkpoint-integration"


STORAGE_ROOT = Path("storage/database/sessions")


# =============================================================
# CONTROLLED CALCULATOR POLICY
# =============================================================


class CalculatorFailurePersistenceActionFilter(ActionFilter):
    """
    Small deterministic Calculator exploration policy.

    Initial exploration exists only to produce a real graph,
    memory, and root state for the persistence test.
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

        return action.target in self.ALLOWED_ACTIONS


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

        Failed coordinator step checkpoint:
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

        return self.repository.save(snapshot)

    def load(
        self,
        session_id,
    ):

        return self.repository.load(session_id)

    def exists(
        self,
        session_id,
    ):

        return self.repository.exists(session_id)

    def list_sessions(
        self,
    ):

        return self.repository.list_sessions()


# =============================================================
# CONTROLLED COORDINATOR TARGET
# =============================================================


class ControlledFailureTarget:
    """
    Minimal exploration target required by the coordinator.
    """

    def __init__(
        self,
        state_id: str,
    ):

        self.state_id = state_id


class OneFailureTargetSelector:
    """
    Return exactly one target.

    After the failed step, no work remains.
    """

    def __init__(
        self,
        state_id: str,
    ):

        self.target = ControlledFailureTarget(state_id)

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
# CONTROLLED FAILED STEP EXECUTOR
# =============================================================


class ControlledReplayFailureStepExecutor:
    """
    Produce exactly one controlled failed exploration step.

    The result represents:

        source state selected successfully
            ↓
        replay failed
            ↓
        action execution never succeeded

    The real ExecutionFailureDetector must classify this result.

    This fake exists only at the failure-injection boundary.

    Everything after the result is real:

        - coordinator
        - detector
        - failure record
        - failure store
        - checkpoint manager
        - session serializer
        - repository
        - filesystem
        - deserialization
    """

    FAILURE_DURATION = 1.75

    def __init__(
        self,
    ):

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

        return ExplorationStepResult(
            source_state_id=(source_state_id),
            selected_action=None,
            target_state_id=None,
            transition=None,
            replay_success=False,
            execution_success=False,
            new_state_discovered=False,
            duration=(self.FAILURE_DURATION),
            failure_reason=("REPLAY_FAILED"),
        )


# =============================================================
# HELPERS
# =============================================================


def get_transition_count(
    graph: StateGraph,
) -> int:
    """
    Return total graph transitions.
    """

    return sum(len(transitions) for transitions in graph.edges.values())


# =============================================================
# REAL DURABLE FAILURE INTEGRATION TEST
# =============================================================


def test_calculator_durable_failure_checkpoint():
    """
    Verify that one coordinator-detected failure survives an
    automatic checkpoint and fresh disk reload.
    """

    real_repository = JsonSessionRepository(storage_root=STORAGE_ROOT)

    repository = RecordingJsonSessionRepository(real_repository)

    session_directory = STORAGE_ROOT / SESSION_ID

    if session_directory.exists():

        shutil.rmtree(session_directory)

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

            print("======================================")

            print("PHASE A: INITIAL REAL EXPLORATION")

            print("======================================")

            initial_graph = StateGraph()

            initial_memory = ExplorationMemory()

            action_filter = CalculatorFailurePersistenceActionFilter()

            initial_executor = ActionExecutor()

            initial_replay_engine = ReplayEngine(
                ui,
                initial_executor,
                initial_graph,
            )

            initial_explorer = BFSExplorer(
                ui=ui,
                executor=initial_executor,
                graph=initial_graph,
                memory=initial_memory,
                replay_engine=(initial_replay_engine),
                executable="calc.exe",
                window_title="Calculator",
                action_filter=action_filter,
                limits=ExplorationLimits(
                    max_states=20,
                    max_actions=12,
                    max_transitions=20,
                    max_depth=2,
                    max_duration=120.0,
                    max_failures=10,
                ),
            )

            initial_result = initial_explorer.explore(window)

            print()

            print("===== INITIAL EXPLORATION RESULT =====")

            print(initial_result)

            root_state_id = initial_result.root_state_id

            assert root_state_id is not None

            assert initial_graph.get_state(root_state_id) is not None

            initial_state_count = len(initial_graph.states)

            initial_transition_count = get_transition_count(initial_graph)

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
            # SAVE INITIAL CLEAN SESSION
            #
            # This is the only manual save in the test.
            # =================================================

            print()

            print("======================================")

            print("PHASE B: SAVE INITIAL SESSION")

            print("======================================")

            created_at = datetime.now()

            initial_snapshot = ExplorationSessionSnapshot(
                schema_version=(SessionSerializer.CURRENT_SCHEMA_VERSION),
                session_id=SESSION_ID,
                root_state_id=(root_state_id),
                status=(SessionStatus.CREATED),
                created_at=(created_at),
                updated_at=(created_at),
                graph=initial_graph,
                memory=initial_memory,
                failures=[],
            )

            initial_saved_path = repository.save(initial_snapshot)

            assert initial_saved_path.is_file()

            assert repository.save_calls == 1

            print(
                "Initial Session Saved:",
                initial_saved_path,
            )

            # =================================================
            # PHASE C
            # LOAD FRESH SESSION OBJECTS
            # =================================================

            print()

            print("======================================")

            print("PHASE C: LOAD FRESH SESSION")

            print("======================================")

            loaded_snapshot = repository.load(SESSION_ID)

            resumed_graph = loaded_snapshot.graph

            resumed_memory = loaded_snapshot.memory

            assert resumed_graph is not initial_graph

            assert resumed_memory is not initial_memory

            assert loaded_snapshot.failures == []

            assert loaded_snapshot.root_state_id == root_state_id

            assert len(resumed_graph.states) == initial_state_count

            assert get_transition_count(resumed_graph) == initial_transition_count

            print(
                "Loaded Failure Count:",
                len(loaded_snapshot.failures),
            )

            # =================================================
            # PHASE D
            # BUILD DURABLE FAILURE RUNTIME
            # =================================================

            print()

            print("======================================")

            print("PHASE D: BUILD FAILURE RUNTIME")

            print("======================================")

            failure_store = FailureStore()

            failure_detector = ExecutionFailureDetector()

            target_selector = OneFailureTargetSelector(state_id=(root_state_id))

            step_executor = ControlledReplayFailureStepExecutor()

            checkpoint_manager = CheckpointManager(
                session_id=SESSION_ID,
                root_state_id=(loaded_snapshot.root_state_id),
                graph=resumed_graph,
                memory=resumed_memory,
                repository=repository,
                created_at=(loaded_snapshot.created_at),
                status=(SessionStatus.RUNNING),
                failure_store=(failure_store),
            )

            coordinator = ExplorationCoordinator(
                target_selector=(target_selector),
                step_executor=(step_executor),
                limits=(
                    CoordinatorLimits(
                        max_steps=5,
                        max_duration=120.0,
                        max_failures=5,
                    )
                ),
                checkpoint_manager=(checkpoint_manager),
                failure_detector=(failure_detector),
                failure_store=(failure_store),
            )

            # =================================================
            # PHASE E
            # RUN ONE FAILED COORDINATOR STEP
            #
            # Required runtime order:
            #
            #     failed result
            #         ↓
            #     detector
            #         ↓
            #     failure store
            #         ↓
            #     checkpoint
            #
            # If checkpointing happened before failure storage,
            # the final disk assertion would fail.
            # =================================================

            print()

            print("======================================")

            print("PHASE E: RUN FAILED STEP")

            print("======================================")

            coordinator_result = coordinator.run(
                root_state_id=(loaded_snapshot.root_state_id)
            )

            print()

            print("===== COORDINATOR RESULT =====")

            print(
                "Steps:",
                coordinator_result.steps,
            )

            print(
                "Successful Steps:",
                coordinator_result.successful_steps,
            )

            print(
                "Failed Steps:",
                coordinator_result.failed_steps,
            )

            print(
                "Structured Failures:",
                len(coordinator_result.failures),
            )

            print(
                "Stop Reason:",
                coordinator_result.stop_reason,
            )

            # =================================================
            # VERIFY COORDINATOR RESULT
            # =================================================

            assert coordinator_result.steps == 1

            assert coordinator_result.successful_steps == 0

            assert coordinator_result.failed_steps == 1

            assert (
                coordinator_result.stop_reason
                == CoordinatorStopReason.NO_REMAINING_TARGETS
            )

            assert len(coordinator_result.failures) == 1

            # =================================================
            # VERIFY LIVE FAILURE STORE
            # =================================================

            assert failure_store.count == 1

            live_failure = failure_store.failures[0]

            assert live_failure is coordinator_result.failures[0]

            assert live_failure.failure_type == FailureType.REPLAY_FAILED

            assert live_failure.source_state_id == root_state_id

            live_failure_id = live_failure.failure_id

            live_failure_timestamp = live_failure.timestamp

            live_failure_message = live_failure.message

            live_failure_metadata = dict(live_failure.metadata)

            print()

            print("===== LIVE STRUCTURED FAILURE =====")

            print(
                "Failure ID:",
                live_failure_id,
            )

            print(
                "Failure Type:",
                live_failure.failure_type,
            )

            print(
                "Source State:",
                live_failure.source_state_id,
            )

            print(
                "Timestamp:",
                live_failure_timestamp,
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
            #     automatic checkpoint after failed step
            # =================================================

            assert repository.save_calls == 2, (
                "Expected one initial manual save "
                "and one automatic failed-step "
                "checkpoint."
            )

            assert checkpoint_manager.last_checkpoint_at is not None

            # =================================================
            # CRITICAL TEST BOUNDARY
            #
            # DO NOT CALL:
            #
            #     repository.save(...)
            #
            # The failure must already exist on disk because the
            # coordinator automatically checkpointed it.
            # =================================================

            # =================================================
            # PHASE F
            # LOAD SESSION DIRECTLY FROM DISK
            # =================================================

            print()

            print("======================================")

            print("PHASE F: LOAD FAILURE FROM DISK")

            print("======================================")

            final_snapshot = real_repository.load(SESSION_ID)

            # =================================================
            # VERIFY FRESH RECONSTRUCTION BOUNDARY
            # =================================================

            assert final_snapshot.graph is not resumed_graph

            assert final_snapshot.memory is not resumed_memory

            assert final_snapshot.failures is not failure_store.failures

            # =================================================
            # VERIFY SESSION METADATA
            # =================================================

            assert final_snapshot.session_id == SESSION_ID

            assert final_snapshot.root_state_id == root_state_id

            assert final_snapshot.created_at == created_at

            assert final_snapshot.updated_at == checkpoint_manager.last_checkpoint_at

            assert final_snapshot.status == SessionStatus.RUNNING

            # =================================================
            # VERIFY FAILURE SURVIVED DISK ROUND-TRIP
            # =================================================

            assert len(final_snapshot.failures) == 1

            disk_failure = final_snapshot.failures[0]

            # Fresh reconstructed object.

            assert disk_failure is not live_failure

            # Stable identity survived.

            assert disk_failure.failure_id == live_failure_id

            # Enum survived and was reconstructed.

            assert disk_failure.failure_type == FailureType.REPLAY_FAILED

            assert isinstance(
                disk_failure.failure_type,
                FailureType,
            )

            # Source context survived.

            assert disk_failure.source_state_id == root_state_id

            # Failure description survived.

            assert disk_failure.message == live_failure_message

            # Timestamp survived.

            assert disk_failure.timestamp == live_failure_timestamp

            # Metadata survived.

            assert disk_failure.metadata == live_failure_metadata

            # Replay failure did not execute an action.

            assert disk_failure.action is None

            assert disk_failure.target_state_id is None

            # =================================================
            # VERIFY GRAPH AND MEMORY WERE NOT CORRUPTED
            # =================================================

            assert len(final_snapshot.graph.states) == len(resumed_graph.states)

            assert get_transition_count(final_snapshot.graph) == get_transition_count(
                resumed_graph
            )

            # =================================================
            # FINAL RESULT
            # =================================================

            print()

            print("======================================")

            print("DURABLE FAILURE CHECKPOINT VERIFIED")

            print("======================================")

            print(
                "Coordinator Steps:",
                coordinator_result.steps,
            )

            print(
                "Failed Steps:",
                coordinator_result.failed_steps,
            )

            print(
                "Live Failure Count:",
                failure_store.count,
            )

            print(
                "Disk Failure Count:",
                len(final_snapshot.failures),
            )

            print(
                "Failure ID Preserved:",
                (disk_failure.failure_id == live_failure_id),
            )

            print(
                "Failure Type Preserved:",
                (disk_failure.failure_type == live_failure.failure_type),
            )

            print(
                "Failure Metadata Preserved:",
                (disk_failure.metadata == live_failure.metadata),
            )

            print(
                "Initial Manual Saves:",
                1,
            )

            print(
                "Automatic Failure Checkpoints:",
                1,
            )

            print(
                "Total Repository Saves:",
                repository.save_calls,
            )

            print(
                "Disk Matches Live Failure:",
                (
                    disk_failure.failure_id == live_failure.failure_id
                    and disk_failure.failure_type == live_failure.failure_type
                    and disk_failure.metadata == live_failure.metadata
                ),
            )

            print()

            print("CALCULATOR DURABLE FAILURE " "CHECKPOINT TEST PASSED")

    finally:

        if session_directory.exists():

            shutil.rmtree(session_directory)


if __name__ == "__main__":

    test_calculator_durable_failure_checkpoint()
