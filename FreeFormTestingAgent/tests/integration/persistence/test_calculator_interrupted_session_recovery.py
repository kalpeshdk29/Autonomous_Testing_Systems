"""
File:
    test_calculator_interrupted_session_recovery.py

Purpose:
    Verify real interrupted-session detection and recovery using
    the Windows Calculator application.

Complete Flow:

    Runtime A
        ↓
    Initial BFS Exploration
        ↓
    CheckpointManager.mark_running()
        ↓
    RUNNING persisted to disk
        ↓
    Coordinator continues exploration
        ↓
    Automatic checkpoints preserve RUNNING
        ↓
    Simulated unexpected termination
        ↓
    NO mark_completed()
        ↓

    Runtime B
        ↓
    Load session from disk
        ↓
    Detect was_interrupted == True
        ↓
    Rebuild fresh runtime from loaded Graph + Memory
        ↓
    Continue autonomous exploration
        ↓
    Automatic checkpoints continue
        ↓
    mark_completed()
        ↓
    Load session from disk again
        ↓
    Verify COMPLETED
        ↓
    Verify was_interrupted == False

Critical Rule:
    Runtime A must not call mark_completed() or mark_failed().

    The persisted RUNNING state is the deterministic evidence that
    the previous runtime ended unexpectedly.
"""

import shutil

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

from agent.persistence.session_status import (
    SessionStatus,
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
    "calculator-interrupted-session-recovery"
)


STORAGE_ROOT = Path(
    "storage/database/sessions"
)


RUNTIME_A_STEPS = 2


RUNTIME_B_STEPS = 2


# =============================================================
# CONTROLLED CALCULATOR POLICY
# =============================================================


class CalculatorRecoveryActionFilter(
    ActionFilter
):
    """
    Controlled Calculator action policy.

    The same policy is used for:

        - initial BFS exploration
        - Runtime A continuation
        - Runtime B recovery
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

    The real repository still performs all filesystem operations.

    This wrapper only counts save calls so the integration test
    can verify lifecycle and automatic-checkpoint persistence.
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
    Return the total number of graph transitions.
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
    Return stable eligible-coverage values.
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


def print_runtime_state(
    title: str,
    graph: StateGraph,
    memory: ExplorationMemory,
    action_filter: ActionFilter,
):
    """
    Print graph and coverage diagnostics.
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


def build_continuation_coordinator(
    ui,
    graph,
    memory,
    action_filter,
    checkpoint_manager,
    max_steps,
):
    """
    Build a fresh autonomous continuation runtime.

    This helper intentionally creates fresh runtime components:

        ActionExecutor
        ReplayEngine
        CoverageEngine
        ExplorationTargetSelector
        ActionSelector
        ExplorationStepExecutor
        ExplorationCoordinator

    Graph and memory are supplied by the caller.
    """

    executor = ActionExecutor()

    replay_engine = ReplayEngine(
        ui,
        executor,
        graph,
    )

    coverage_engine = CoverageEngine(
        graph=graph,
        memory=memory,
        action_filter=action_filter,
    )

    target_selector = (
        ExplorationTargetSelector(
            coverage_engine=(
                coverage_engine
            ),

            strategy=(
                ShallowestFirstStrategy()
            ),

            max_depth=2,
        )
    )

    action_selector = (
        ActionSelector(
            memory=memory,

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

            executor=executor,

            graph=graph,

            memory=memory,

            replay_engine=(
                replay_engine
            ),

            action_selector=(
                action_selector
            ),

            executable="calc.exe",

            window_title="Calculator",
        )
    )

    return ExplorationCoordinator(
        target_selector=(
            target_selector
        ),

        step_executor=(
            step_executor
        ),

        limits=(
            CoordinatorLimits(
                max_steps=max_steps,

                max_duration=120.0,

                max_failures=3,
            )
        ),

        checkpoint_manager=(
            checkpoint_manager
        ),
    )


# =============================================================
# REAL INTERRUPTED SESSION RECOVERY TEST
# =============================================================


def test_calculator_interrupted_session_recovery():
    """
    Verify real interrupted-session detection and recovery.

    Runtime A:
        1. Performs initial BFS exploration.
        2. Persists RUNNING.
        3. Continues for two autonomous steps.
        4. Stops without persisting a terminal status.

    Runtime B:
        1. Loads the RUNNING session.
        2. Detects interruption.
        3. Rebuilds fresh runtime components.
        4. Continues exploration.
        5. Persists COMPLETED.
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
                CalculatorRecoveryActionFilter()
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

            print_runtime_state(
                title="INITIAL RUNTIME",
                graph=initial_graph,
                memory=initial_memory,
                action_filter=action_filter,
            )

            # =================================================
            # PHASE B
            # RUNTIME A STARTS
            #
            # mark_running() is the first durable lifecycle save.
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE B: RUNTIME A STARTS"
            )

            print(
                "======================================"
            )

            runtime_a_checkpoint_manager = (
                CheckpointManager(
                    session_id=SESSION_ID,

                    root_state_id=(
                        root_state_id
                    ),

                    graph=initial_graph,

                    memory=initial_memory,

                    repository=repository,
                )
            )

            running_snapshot = (
                runtime_a_checkpoint_manager
                .mark_running()
            )

            assert (
                running_snapshot.status
                ==
                SessionStatus.RUNNING
            )

            assert (
                runtime_a_checkpoint_manager.status
                ==
                SessionStatus.RUNNING
            )

            assert running_snapshot.was_interrupted

            assert repository.save_calls == 1

            created_at = (
                running_snapshot.created_at
            )

            print(
                "Persisted Status:",
                running_snapshot.status,
            )

            print(
                "Repository Saves:",
                repository.save_calls,
            )

            # =================================================
            # PHASE C
            # RUNTIME A AUTONOMOUS CONTINUATION
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE C: RUNTIME A CONTINUATION"
            )

            print(
                "======================================"
            )

            runtime_a_coordinator = (
                build_continuation_coordinator(
                    ui=ui,

                    graph=initial_graph,

                    memory=initial_memory,

                    action_filter=action_filter,

                    checkpoint_manager=(
                        runtime_a_checkpoint_manager
                    ),

                    max_steps=(
                        RUNTIME_A_STEPS
                    ),
                )
            )

            runtime_a_result = (
                runtime_a_coordinator.run(
                    root_state_id=(
                        root_state_id
                    )
                )
            )

            print()

            print(
                "===== RUNTIME A RESULT ====="
            )

            print(
                "Steps:",
                runtime_a_result.steps,
            )

            print(
                "Successful Steps:",
                runtime_a_result.successful_steps,
            )

            print(
                "Failed Steps:",
                runtime_a_result.failed_steps,
            )

            print(
                "New States:",
                runtime_a_result.new_states,
            )

            print(
                "Stop Reason:",
                runtime_a_result.stop_reason,
            )

            assert (
                runtime_a_result.steps
                ==
                RUNTIME_A_STEPS
            )

            assert (
                runtime_a_result.successful_steps
                ==
                RUNTIME_A_STEPS
            )

            assert (
                runtime_a_result.failed_steps
                ==
                0
            )

            expected_runtime_a_saves = (
                1
                +
                RUNTIME_A_STEPS
            )

            assert (
                repository.save_calls
                ==
                expected_runtime_a_saves
            )

            assert (
                runtime_a_checkpoint_manager.status
                ==
                SessionStatus.RUNNING
            )

            print_runtime_state(
                title="RUNTIME A BEFORE INTERRUPTION",
                graph=initial_graph,
                memory=initial_memory,
                action_filter=action_filter,
            )

            # =================================================
            # SIMULATED UNEXPECTED TERMINATION
            #
            # DO NOT CALL:
            #
            #     runtime_a_checkpoint_manager.mark_completed()
            #
            # DO NOT CALL:
            #
            #     runtime_a_checkpoint_manager.mark_failed()
            #
            # DO NOT CALL:
            #
            #     repository.save(...)
            #
            # Runtime A disappears while the latest durable
            # lifecycle status remains RUNNING.
            # =================================================

            # =================================================
            # PHASE D
            # RUNTIME B LOADS THE SESSION
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE D: LOAD AFTER INTERRUPTION"
            )

            print(
                "======================================"
            )

            interrupted_snapshot = (
                real_repository.load(
                    SESSION_ID
                )
            )

            assert (
                interrupted_snapshot.status
                ==
                SessionStatus.RUNNING
            )

            assert (
                interrupted_snapshot.was_interrupted
            )

            assert (
                interrupted_snapshot.root_state_id
                ==
                root_state_id
            )

            assert (
                interrupted_snapshot.created_at
                ==
                created_at
            )

            print()

            print(
                "======================================"
            )

            print(
                "INTERRUPTED SESSION DETECTED"
            )

            print(
                "======================================"
            )

            print(
                "Status:",
                interrupted_snapshot.status,
            )

            print(
                "Was Interrupted:",
                interrupted_snapshot
                .was_interrupted,
            )

            print(
                "States:",
                len(
                    interrupted_snapshot
                    .graph
                    .states
                ),
            )

            print(
                "Transitions:",
                get_transition_count(
                    interrupted_snapshot.graph
                ),
            )

            # =================================================
            # CAPTURE KNOWLEDGE BEFORE RECOVERY
            # =================================================

            recovered_graph = (
                interrupted_snapshot.graph
            )

            recovered_memory = (
                interrupted_snapshot.memory
            )

            transitions_before_recovery = (
                get_transition_count(
                    recovered_graph
                )
            )

            coverage_before_recovery = (
                get_coverage_values(
                    graph=recovered_graph,

                    memory=recovered_memory,

                    action_filter=action_filter,
                )
            )

            print_runtime_state(
                title="RECOVERED DURABLE STATE",
                graph=recovered_graph,
                memory=recovered_memory,
                action_filter=action_filter,
            )

            # =================================================
            # PHASE E
            # BUILD FRESH RUNTIME B
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE E: BUILD RECOVERY RUNTIME"
            )

            print(
                "======================================"
            )

            runtime_b_checkpoint_manager = (
                CheckpointManager(
                    session_id=SESSION_ID,

                    root_state_id=(
                        interrupted_snapshot
                        .root_state_id
                    ),

                    graph=recovered_graph,

                    memory=recovered_memory,

                    repository=repository,

                    created_at=(
                        interrupted_snapshot
                        .created_at
                    ),

                    status=(
                        interrupted_snapshot
                        .status
                    ),
                )
            )

            assert (
                runtime_b_checkpoint_manager.status
                ==
                SessionStatus.RUNNING
            )

            runtime_b_coordinator = (
                build_continuation_coordinator(
                    ui=ui,

                    graph=recovered_graph,

                    memory=recovered_memory,

                    action_filter=action_filter,

                    checkpoint_manager=(
                        runtime_b_checkpoint_manager
                    ),

                    max_steps=(
                        RUNTIME_B_STEPS
                    ),
                )
            )

            # =================================================
            # PHASE F
            # RECOVER AND CONTINUE
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE F: RECOVER AND CONTINUE"
            )

            print(
                "======================================"
            )

            runtime_b_result = (
                runtime_b_coordinator.run(
                    root_state_id=(
                        interrupted_snapshot
                        .root_state_id
                    )
                )
            )

            print()

            print(
                "===== RUNTIME B RESULT ====="
            )

            print(
                "Steps:",
                runtime_b_result.steps,
            )

            print(
                "Successful Steps:",
                runtime_b_result.successful_steps,
            )

            print(
                "Failed Steps:",
                runtime_b_result.failed_steps,
            )

            print(
                "New States:",
                runtime_b_result.new_states,
            )

            print(
                "Stop Reason:",
                runtime_b_result.stop_reason,
            )

            assert (
                runtime_b_result.steps
                ==
                RUNTIME_B_STEPS
            )

            assert (
                runtime_b_result.successful_steps
                ==
                RUNTIME_B_STEPS
            )

            assert (
                runtime_b_result.failed_steps
                ==
                0
            )

            transitions_after_recovery = (
                get_transition_count(
                    recovered_graph
                )
            )

            coverage_after_recovery = (
                get_coverage_values(
                    graph=recovered_graph,

                    memory=recovered_memory,

                    action_filter=action_filter,
                )
            )

            assert (
                transitions_after_recovery
                >
                transitions_before_recovery
            )

            assert (
                coverage_after_recovery[
                    "eligible_explored_actions"
                ]
                >
                coverage_before_recovery[
                    "eligible_explored_actions"
                ]
            )

            assert (
                runtime_b_checkpoint_manager.status
                ==
                SessionStatus.RUNNING
            )

            print_runtime_state(
                title="RUNTIME B AFTER RECOVERY",
                graph=recovered_graph,
                memory=recovered_memory,
                action_filter=action_filter,
            )

            # =================================================
            # PHASE G
            # CLEAN COMPLETION
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE G: MARK SESSION COMPLETED"
            )

            print(
                "======================================"
            )

            completed_snapshot = (
                runtime_b_checkpoint_manager
                .mark_completed()
            )

            assert (
                completed_snapshot.status
                ==
                SessionStatus.COMPLETED
            )

            assert (
                runtime_b_checkpoint_manager.status
                ==
                SessionStatus.COMPLETED
            )

            assert (
                not completed_snapshot.was_interrupted
            )

            # =================================================
            # PHASE H
            # FINAL FRESH DISK LOAD
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE H: LOAD COMPLETED SESSION"
            )

            print(
                "======================================"
            )

            final_snapshot = (
                real_repository.load(
                    SESSION_ID
                )
            )

            assert (
                final_snapshot.status
                ==
                SessionStatus.COMPLETED
            )

            assert (
                not final_snapshot.was_interrupted
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
                get_transition_count(
                    final_snapshot.graph
                )
                ==
                transitions_after_recovery
            )

            final_coverage = (
                get_coverage_values(
                    graph=final_snapshot.graph,

                    memory=final_snapshot.memory,

                    action_filter=action_filter,
                )
            )

            assert (
                final_coverage
                ==
                coverage_after_recovery
            )

            print_runtime_state(
                title="FINAL COMPLETED STATE FROM DISK",
                graph=final_snapshot.graph,
                memory=final_snapshot.memory,
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
                "INTERRUPTED SESSION RECOVERY VERIFIED"
            )

            print(
                "======================================"
            )

            print(
                "Runtime A Steps:",
                runtime_a_result.steps,
            )

            print(
                "Interrupted Status:",
                interrupted_snapshot.status,
            )

            print(
                "Interruption Detected:",
                interrupted_snapshot
                .was_interrupted,
            )

            print(
                "Runtime B Recovery Steps:",
                runtime_b_result.steps,
            )

            print(
                "Transitions Before Recovery:",
                transitions_before_recovery,
            )

            print(
                "Transitions After Recovery:",
                transitions_after_recovery,
            )

            print(
                "Explored Actions Before Recovery:",
                coverage_before_recovery[
                    "eligible_explored_actions"
                ],
            )

            print(
                "Explored Actions After Recovery:",
                coverage_after_recovery[
                    "eligible_explored_actions"
                ],
            )

            print(
                "Final Status:",
                final_snapshot.status,
            )

            print(
                "Final Was Interrupted:",
                final_snapshot.was_interrupted,
            )

            print(
                "Disk Matches Recovered Runtime:",
                (
                    final_coverage
                    ==
                    coverage_after_recovery
                ),
            )

            print(
                "Total Repository Saves:",
                repository.save_calls,
            )

            print()

            print(
                "CALCULATOR INTERRUPTED SESSION "
                "RECOVERY TEST PASSED"
            )

    finally:

        if session_directory.exists():

            shutil.rmtree(
                session_directory
            )


if __name__ == "__main__":

    test_calculator_interrupted_session_recovery()