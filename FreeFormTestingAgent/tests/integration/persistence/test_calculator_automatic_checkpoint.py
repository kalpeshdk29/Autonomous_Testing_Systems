"""
File:
    test_calculator_automatic_checkpoint.py

Purpose:
    Verify automatic durable checkpointing during real Calculator
    continuation exploration.

Complete Flow:

    Real Calculator
        ↓
    Initial BFS Exploration
        ↓
    Save Initial Session
        ↓
    Load Fresh Graph + Memory
        ↓
    Build Fresh Continuation Runtime
        ↓
    Attach Real CheckpointManager
        ↓
    ExplorationCoordinator
        ↓
    Step 1 → Automatic Checkpoint
    Step 2 → Automatic Checkpoint
    Step 3 → Automatic Checkpoint
        ↓
    Load Final Session Directly From Disk
        ↓
    Verify Disk State Matches Live Runtime

Critical Rule:

    After coordinator.run() completes, this test does NOT manually
    save the session.

    Therefore, the final persisted state can exist only because
    automatic coordinator checkpointing worked.
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

from agent.coordinator.exploration_coordinator import (
    ExplorationCoordinator,
)


from agent.coverage.coverage_engine import (
    CoverageEngine,
)


from agent.executor.action_executor import (
    ActionExecutor,
)

from agent.explorer.exploration_step_executor import (
    ExplorationStepExecutor,
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


from agent.replay.replay_engine import (
    ReplayEngine,
)


from agent.strategy.action.deterministic_action_strategy import (
    DeterministicActionStrategy,
)

from agent.strategy.action import (
    ActionSelector,
)

from agent.strategy.exploration_target_selector import (
    ExplorationTargetSelector,
)

from agent.strategy.shallowest_first_strategy import (
    ShallowestFirstStrategy,
)


# =============================================================
# TEST CONFIGURATION
# =============================================================


SESSION_ID = (
    "calculator-automatic-checkpoint-integration"
)


STORAGE_ROOT = Path(
    "storage/database/sessions"
)


CONTINUATION_STEPS = 3


# =============================================================
# CONTROLLED CALCULATOR POLICY
# =============================================================


class CalculatorCheckpointActionFilter(
    ActionFilter
):
    """
    Controlled Calculator action policy.

    The same policy is used for:

        - initial BFS exploration
        - resumed target selection
        - resumed action selection
        - coverage comparison
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

    Purpose:
        Preserve real filesystem behavior while counting saves.

    This lets the test prove:

        initial manual save = 1

        continuation checkpoints = coordinator steps

    The decorator does not replace or fake persistence.
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
        return self.repository.list_sessions()


# =============================================================
# HELPERS
# =============================================================


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


def get_coverage_values(
    graph: StateGraph,
    memory: ExplorationMemory,
    action_filter: ActionFilter,
) -> dict:
    """
    Return stable eligible coverage values.
    """

    engine = CoverageEngine(
        graph=graph,
        memory=memory,
        action_filter=action_filter,
    )

    report = engine.calculate_report()

    return {
        "total_states": (
            report.total_states
        ),

        "eligible_total_actions": (
            report.eligible_total_actions
        ),

        "eligible_explored_actions": (
            report.eligible_explored_actions
        ),

        "eligible_unexplored_actions": (
            report.eligible_unexplored_actions
        ),

        "eligible_action_coverage_percentage": (
            report
            .eligible_action_coverage_percentage
        ),
    }


def get_executed_action_keys(
    graph: StateGraph,
    memory: ExplorationMemory,
) -> set[tuple[str, str]]:
    """
    Return observable executed-action knowledge.
    """

    executed = set()

    for node in graph.states.values():

        state = node.state

        for action in state.available_actions:

            if memory.is_executed(
                state.state_hash,
                action.target,
            ):

                executed.add(
                    (
                        state.state_hash,
                        action.target,
                    )
                )

    return executed


def print_runtime_state(
    title: str,
    graph: StateGraph,
    memory: ExplorationMemory,
    action_filter: ActionFilter,
):
    """
    Print compact graph and coverage diagnostics.
    """

    coverage = get_coverage_values(
        graph=graph,
        memory=memory,
        action_filter=action_filter,
    )

    print()

    print(
        "======================================"
    )

    print(title)

    print(
        "======================================"
    )

    print(
        "States:",
        len(graph.states),
    )

    print(
        "Transitions:",
        get_transition_count(
            graph
        ),
    )

    print(
        "Eligible Actions:",
        coverage[
            "eligible_total_actions"
        ],
    )

    print(
        "Explored Eligible Actions:",
        coverage[
            "eligible_explored_actions"
        ],
    )

    print(
        "Unexplored Eligible Actions:",
        coverage[
            "eligible_unexplored_actions"
        ],
    )

    print(
        "Eligible Coverage:",
        coverage[
            "eligible_action_coverage_percentage"
        ],
    )


# =============================================================
# REAL AUTOMATIC CHECKPOINT INTEGRATION TEST
# =============================================================


def test_calculator_automatic_checkpoint():
    """
    Verify that the real coordinator automatically persists every
    continuation step through CheckpointManager.
    """

    real_repository = (
        JsonSessionRepository(
            storage_root=STORAGE_ROOT
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
                "PHASE A: INITIAL EXPLORATION"
            )

            print(
                "======================================"
            )

            initial_graph = StateGraph()

            initial_memory = (
                ExplorationMemory()
            )

            action_filter = (
                CalculatorCheckpointActionFilter()
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

            initial_explorer = BFSExplorer(
                ui=ui,

                executor=initial_executor,

                graph=initial_graph,

                memory=initial_memory,

                replay_engine=(
                    initial_replay_engine
                ),

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

            initial_result = (
                initial_explorer.explore(
                    window
                )
            )

            print()

            print(
                "===== INITIAL EXPLORATION RESULT ====="
            )

            print(initial_result)

            root_state_id = (
                initial_result.root_state_id
            )

            assert root_state_id is not None

            assert (
                initial_graph.get_state(
                    root_state_id
                )
                is not None
            )

            # =================================================
            # CAPTURE INITIAL KNOWLEDGE
            # =================================================

            initial_coverage = (
                get_coverage_values(
                    graph=initial_graph,
                    memory=initial_memory,
                    action_filter=action_filter,
                )
            )

            initial_transitions = (
                get_transition_count(
                    initial_graph
                )
            )

            initial_executed_actions = (
                get_executed_action_keys(
                    graph=initial_graph,
                    memory=initial_memory,
                )
            )

            print_runtime_state(
                title="BEFORE INITIAL SAVE",
                graph=initial_graph,
                memory=initial_memory,
                action_filter=action_filter,
            )

            # =================================================
            # PHASE B
            # SAVE INITIAL SESSION V1
            #
            # This is the only manual save in the test.
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE B: SAVE INITIAL SESSION"
            )

            print(
                "======================================"
            )

            created_at = datetime.now()

            initial_snapshot = (
                ExplorationSessionSnapshot(
                    schema_version=(
                        SessionSerializer
                        .CURRENT_SCHEMA_VERSION
                    ),

                    session_id=SESSION_ID,

                    root_state_id=(
                        root_state_id
                    ),

                    created_at=created_at,

                    updated_at=created_at,

                    graph=initial_graph,

                    memory=initial_memory,
                )
            )

            initial_saved_path = (
                repository.save(
                    initial_snapshot
                )
            )

            assert initial_saved_path.is_file()

            assert repository.save_calls == 1

            print(
                "Initial Session Saved:",
                initial_saved_path,
            )

            # =================================================
            # PHASE C
            # LOAD FRESH RUNTIME OBJECTS
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE C: LOAD SESSION"
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
                is not initial_graph
            )

            assert (
                resumed_memory
                is not initial_memory
            )

            assert (
                loaded_snapshot.root_state_id
                ==
                root_state_id
            )

            assert (
                get_coverage_values(
                    graph=resumed_graph,
                    memory=resumed_memory,
                    action_filter=action_filter,
                )
                ==
                initial_coverage
            )

            assert (
                get_transition_count(
                    resumed_graph
                )
                ==
                initial_transitions
            )

            assert (
                get_executed_action_keys(
                    graph=resumed_graph,
                    memory=resumed_memory,
                )
                ==
                initial_executed_actions
            )

            # =================================================
            # PHASE D
            # BUILD FRESH RESUME RUNTIME
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE D: BUILD CHECKPOINTED RUNTIME"
            )

            print(
                "======================================"
            )

            resumed_executor = (
                ActionExecutor()
            )

            resumed_replay_engine = (
                ReplayEngine(
                    ui,
                    resumed_executor,
                    resumed_graph,
                )
            )

            resumed_coverage_engine = (
                CoverageEngine(
                    graph=resumed_graph,

                    memory=resumed_memory,

                    action_filter=(
                        action_filter
                    ),
                )
            )

            target_selector = (
                ExplorationTargetSelector(
                    coverage_engine=(
                        resumed_coverage_engine
                    ),

                    strategy=(
                        ShallowestFirstStrategy()
                    ),

                    max_depth=2,
                )
            )

            action_selector = (
                ActionSelector(
                    memory=resumed_memory,

                    action_filter=(
                        action_filter
                    ),

                    strategy=(
                        DeterministicActionStrategy()
                    ),
                )
            )

            step_executor = (
                ExplorationStepExecutor(
                    ui=ui,

                    executor=resumed_executor,

                    graph=resumed_graph,

                    memory=resumed_memory,

                    replay_engine=(
                        resumed_replay_engine
                    ),

                    action_selector=(
                        action_selector
                    ),

                    executable="calc.exe",

                    window_title="Calculator",
                )
            )

            # =================================================
            # REAL CHECKPOINT MANAGER
            # =================================================

            checkpoint_manager = (
                CheckpointManager(
                    session_id=SESSION_ID,

                    root_state_id=(
                        loaded_snapshot
                        .root_state_id
                    ),

                    graph=resumed_graph,

                    memory=resumed_memory,

                    repository=repository,

                    created_at=(
                        loaded_snapshot
                        .created_at
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
                            max_steps=(
                                CONTINUATION_STEPS
                            ),

                            max_duration=120.0,

                            max_failures=3,
                        )
                    ),

                    checkpoint_manager=(
                        checkpoint_manager
                    ),
                )
            )

            # =================================================
            # PHASE E
            # RUN AUTOMATICALLY CHECKPOINTED CONTINUATION
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE E: AUTOMATIC CHECKPOINT CONTINUATION"
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
                coordinator_result.successful_steps,
            )

            print(
                "Failed Steps:",
                coordinator_result.failed_steps,
            )

            print(
                "New States:",
                coordinator_result.new_states,
            )

            print(
                "Stop Reason:",
                coordinator_result.stop_reason,
            )

            # =================================================
            # VERIFY COORDINATOR EXECUTION
            # =================================================

            assert (
                coordinator_result.steps
                ==
                CONTINUATION_STEPS
            )

            assert (
                coordinator_result.successful_steps
                ==
                CONTINUATION_STEPS
            )

            assert (
                coordinator_result.failed_steps
                ==
                0
            )

            # One initial manual save plus one automatic save
            # after every continuation step.

            expected_save_calls = (
                1
                +
                coordinator_result.steps
            )

            assert (
                repository.save_calls
                ==
                expected_save_calls
            ), (
                "Unexpected number of repository saves. "
                f"Expected {expected_save_calls}, "
                f"received {repository.save_calls}."
            )

            assert (
                checkpoint_manager
                .last_checkpoint_at
                is not None
            )

            # =================================================
            # CAPTURE FINAL LIVE RUNTIME
            # =================================================

            live_coverage = (
                get_coverage_values(
                    graph=resumed_graph,
                    memory=resumed_memory,
                    action_filter=action_filter,
                )
            )

            live_transitions = (
                get_transition_count(
                    resumed_graph
                )
            )

            live_executed_actions = (
                get_executed_action_keys(
                    graph=resumed_graph,
                    memory=resumed_memory,
                )
            )

            print_runtime_state(
                title="LIVE RUNTIME AFTER COORDINATOR",
                graph=resumed_graph,
                memory=resumed_memory,
                action_filter=action_filter,
            )

            assert (
                live_transitions
                >
                initial_transitions
            )

            assert (
                live_coverage[
                    "eligible_explored_actions"
                ]
                >
                initial_coverage[
                    "eligible_explored_actions"
                ]
            )

            assert (
                initial_executed_actions
                .issubset(
                    live_executed_actions
                )
            )

            # =================================================
            # CRITICAL TEST BOUNDARY
            #
            # DO NOT CALL:
            #
            #     repository.save(...)
            #
            # here.
            #
            # The final disk state must already exist because the
            # coordinator automatically checkpointed each step.
            # =================================================

            # =================================================
            # PHASE F
            # LOAD FINAL STATE DIRECTLY FROM DISK
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE F: LOAD AUTOMATIC CHECKPOINT"
            )

            print(
                "======================================"
            )

            final_snapshot = (
                real_repository.load(
                    SESSION_ID
                )
            )

            disk_graph = (
                final_snapshot.graph
            )

            disk_memory = (
                final_snapshot.memory
            )

            # Fresh reconstruction boundary.

            assert (
                disk_graph
                is not resumed_graph
            )

            assert (
                disk_memory
                is not resumed_memory
            )

            # =================================================
            # VERIFY SESSION METADATA
            # =================================================

            assert (
                final_snapshot.session_id
                ==
                SESSION_ID
            )

            assert (
                final_snapshot.root_state_id
                ==
                root_state_id
            )

            assert (
                final_snapshot.created_at
                ==
                created_at
            )

            assert (
                final_snapshot.updated_at
                ==
                checkpoint_manager
                .last_checkpoint_at
            )

            assert (
                final_snapshot.updated_at
                >
                final_snapshot.created_at
            )

            # =================================================
            # VERIFY DISK GRAPH == LIVE GRAPH
            # =================================================

            assert (
                len(
                    disk_graph.states
                )
                ==
                len(
                    resumed_graph.states
                )
            )

            assert (
                get_transition_count(
                    disk_graph
                )
                ==
                live_transitions
            )

            # =================================================
            # VERIFY DISK MEMORY == LIVE MEMORY
            # =================================================

            disk_executed_actions = (
                get_executed_action_keys(
                    graph=disk_graph,
                    memory=disk_memory,
                )
            )

            assert (
                disk_executed_actions
                ==
                live_executed_actions
            )

            # =================================================
            # VERIFY DISK COVERAGE == LIVE COVERAGE
            # =================================================

            disk_coverage = (
                get_coverage_values(
                    graph=disk_graph,
                    memory=disk_memory,
                    action_filter=action_filter,
                )
            )

            assert (
                disk_coverage
                ==
                live_coverage
            )

            print_runtime_state(
                title="FINAL STATE LOADED FROM DISK",
                graph=disk_graph,
                memory=disk_memory,
                action_filter=action_filter,
            )

            # =================================================
            # FINAL RESULT
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "AUTOMATIC CHECKPOINT VERIFIED"
            )

            print(
                "======================================"
            )

            print(
                "Coordinator Steps:",
                coordinator_result.steps,
            )

            print(
                "Initial Manual Saves:",
                1,
            )

            print(
                "Automatic Checkpoints:",
                coordinator_result.steps,
            )

            print(
                "Total Repository Saves:",
                repository.save_calls,
            )

            print(
                "Transitions Before:",
                initial_transitions,
            )

            print(
                "Transitions After:",
                live_transitions,
            )

            print(
                "Explored Eligible Before:",
                initial_coverage[
                    "eligible_explored_actions"
                ],
            )

            print(
                "Explored Eligible After:",
                live_coverage[
                    "eligible_explored_actions"
                ],
            )

            print(
                "Disk Matches Live Runtime:",
                (
                    disk_coverage
                    ==
                    live_coverage
                ),
            )

            print(
                "Last Checkpoint:",
                checkpoint_manager
                .last_checkpoint_at,
            )

            print()

            print(
                "CALCULATOR AUTOMATIC CHECKPOINT "
                "TEST PASSED"
            )

    finally:

        # Remove only this integration test's session.

        if session_directory.exists():

            shutil.rmtree(
                session_directory
            )


if __name__ == "__main__":

    test_calculator_automatic_checkpoint()