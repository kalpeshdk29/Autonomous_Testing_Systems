"""
File:
    test_calculator_session_resume.py

Purpose:
    Verify true durable continuation of a real Calculator
    exploration session.

Complete Flow:

    Real Calculator
        ↓
    Initial BFS Exploration
        ↓
    Save Session V1
        ↓
    Load Fresh Graph + Memory
        ↓
    Build Fresh Continuation Runtime
        ↓
    ExplorationCoordinator
        ↓
    Continue Autonomous Exploration
        ↓
    Save Session V2
        ↓
    Load Again
        ↓
    Verify Continued Knowledge Survived

What This Test Proves:

    1. A real Calculator session can be saved.

    2. Fresh graph and memory objects can be loaded.

    3. Historical coverage survives.

    4. Historical executed actions are respected.

    5. The coordinator can select work from loaded knowledge.

    6. Replay can use the persisted root state.

    7. New actions can be executed after loading.

    8. Graph transitions increase after resume.

    9. Explored eligible actions increase after resume.

    10. Unexplored eligible actions decrease after resume.

    11. Eligible coverage increases after resume.

    12. The updated session can be saved again.

    13. The updated session can be loaded again.

    14. Continued exploration knowledge survives the second
        disk round trip.
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
    "calculator-resume-integration"
)


STORAGE_ROOT = Path(
    "storage/database/sessions"
)


# =============================================================
# CONTROLLED CALCULATOR POLICY
# =============================================================


class CalculatorResumeActionFilter(
    ActionFilter
):
    """
    Controlled Calculator action policy.

    Only these actions are eligible:

        7
        8
        +
        =

    The same policy is used:

        - during initial BFS exploration
        - after loading
        - during autonomous continuation
        - during coverage comparison

    This is critical because persisted exploration knowledge is
    meaningful only under the same action eligibility policy.
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
        """
        Return True only for controlled Calculator actions.
        """

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
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
    Calculate stable aggregate eligible coverage values.
    """

    coverage_engine = CoverageEngine(
        graph=graph,
        memory=memory,
        action_filter=action_filter,
    )

    report = (
        coverage_engine.calculate_report()
    )

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

    Each key is:

        (
            state_hash,
            action_target,
        )

    Only public ExplorationMemory behavior is used.
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


def create_session_snapshot(
    session_id: str,
    root_state_id: str,
    graph: StateGraph,
    memory: ExplorationMemory,
    created_at: datetime,
    updated_at: datetime,
) -> ExplorationSessionSnapshot:
    """
    Create one durable session snapshot.
    """

    return ExplorationSessionSnapshot(
        schema_version=(
            SessionSerializer
            .CURRENT_SCHEMA_VERSION
        ),

        session_id=session_id,

        root_state_id=root_state_id,

        created_at=created_at,

        updated_at=updated_at,

        graph=graph,

        memory=memory,
    )


def print_coverage(
    title: str,
    coverage: dict,
    graph: StateGraph,
):
    """
    Print compact continuation diagnostics.
    """

    print()

    print(
        "======================================"
    )

    print(
        title
    )

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
# REAL RESUME INTEGRATION TEST
# =============================================================


def test_calculator_session_resume():
    """
    Perform a complete:

        explore
        save
        load
        resume
        save again
        load again

    cycle using the real Calculator application.
    """

    repository = JsonSessionRepository(
        storage_root=STORAGE_ROOT
    )

    session_directory = (
        STORAGE_ROOT
        /
        SESSION_ID
    )

    # =========================================================
    # TEST ISOLATION
    #
    # Remove only this test's own session.
    # Never clear general project storage.
    # =========================================================

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
            #
            # INITIAL EXPLORATION
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

            initial_executor = (
                ActionExecutor()
            )

            action_filter = (
                CalculatorResumeActionFilter()
            )

            initial_replay_engine = (
                ReplayEngine(
                    ui,
                    initial_executor,
                    initial_graph,
                )
            )

            initial_limits = (
                ExplorationLimits(
                    max_states=20,
                    max_actions=12,
                    max_transitions=20,
                    max_depth=2,
                    max_duration=120.0,
                    max_failures=10,
                )
            )

            initial_explorer = BFSExplorer(
                ui=ui,

                executor=(
                    initial_executor
                ),

                graph=initial_graph,

                memory=initial_memory,

                replay_engine=(
                    initial_replay_engine
                ),

                executable="calc.exe",

                window_title="Calculator",

                action_filter=(
                    action_filter
                ),

                limits=initial_limits,
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

            print(
                initial_result
            )

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

            coverage_before_save = (
                get_coverage_values(
                    graph=initial_graph,
                    memory=initial_memory,
                    action_filter=action_filter,
                )
            )

            transitions_before_resume = (
                get_transition_count(
                    initial_graph
                )
            )

            states_before_resume = len(
                initial_graph.states
            )

            executed_before_resume = (
                get_executed_action_keys(
                    graph=initial_graph,
                    memory=initial_memory,
                )
            )

            assert (
                len(
                    executed_before_resume
                )
                ==
                coverage_before_save[
                    "eligible_explored_actions"
                ]
            )

            print_coverage(
                title="BEFORE FIRST SAVE",
                coverage=coverage_before_save,
                graph=initial_graph,
            )

            # =================================================
            # PHASE B
            #
            # SAVE SESSION V1
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE B: SAVE SESSION V1"
            )

            print(
                "======================================"
            )

            created_at = datetime.now()

            snapshot_v1 = (
                create_session_snapshot(
                    session_id=SESSION_ID,

                    root_state_id=(
                        root_state_id
                    ),

                    graph=initial_graph,

                    memory=initial_memory,

                    created_at=created_at,

                    updated_at=created_at,
                )
            )

            saved_path_v1 = repository.save(
                snapshot_v1
            )

            print(
                "Saved:",
                saved_path_v1,
            )

            assert saved_path_v1.is_file()

            # =================================================
            # PHASE C
            #
            # LOAD FRESH SESSION OBJECTS
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE C: LOAD SESSION V1"
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

            # Prove this is a reconstruction boundary.

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

            # =================================================
            # VERIFY HISTORICAL KNOWLEDGE BEFORE CONTINUATION
            # =================================================

            coverage_after_load = (
                get_coverage_values(
                    graph=resumed_graph,
                    memory=resumed_memory,
                    action_filter=action_filter,
                )
            )

            assert (
                coverage_after_load
                ==
                coverage_before_save
            )

            assert (
                get_transition_count(
                    resumed_graph
                )
                ==
                transitions_before_resume
            )

            assert (
                get_executed_action_keys(
                    graph=resumed_graph,
                    memory=resumed_memory,
                )
                ==
                executed_before_resume
            )

            print_coverage(
                title="AFTER LOAD / BEFORE RESUME",
                coverage=coverage_after_load,
                graph=resumed_graph,
            )

            # =================================================
            # PHASE D
            #
            # BUILD A COMPLETELY FRESH CONTINUATION RUNTIME
            # AROUND THE LOADED GRAPH AND MEMORY
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE D: BUILD FRESH RESUME RUNTIME"
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

            target_strategy = (
                ShallowestFirstStrategy()
            )

            target_selector = (
                ExplorationTargetSelector(
                    coverage_engine=(
                        resumed_coverage_engine
                    ),

                    strategy=(
                        target_strategy
                    ),

                    max_depth=2,
                )
            )

            action_strategy = (
                DeterministicActionStrategy()
            )

            action_selector = (
                ActionSelector(
                    memory=resumed_memory,

                    action_filter=(
                        action_filter
                    ),

                    strategy=(
                        action_strategy
                    ),
                )
            )

            step_executor = (
                ExplorationStepExecutor(
                    ui=ui,

                    executor=(
                        resumed_executor
                    ),

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

            coordinator_limits = (
                CoordinatorLimits(
                    max_steps=3,
                    max_duration=120.0,
                    max_failures=3,
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
                        coordinator_limits
                    ),
                )
            )

            # =================================================
            # PHASE E
            #
            # CONTINUE EXPLORATION FROM PERSISTED KNOWLEDGE
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE E: RESUME AUTONOMOUS EXPLORATION"
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
                "Duration:",
                coordinator_result.duration,
            )

            print(
                "Stop Reason:",
                coordinator_result.stop_reason,
            )

            # =================================================
            # VERIFY CONTINUATION ACTUALLY HAPPENED
            # =================================================

            assert (
                coordinator_result.steps
                >
                0
            ), (
                "Resume coordinator executed no steps."
            )

            assert (
                coordinator_result.successful_steps
                >
                0
            ), (
                "Resume coordinator completed no "
                "successful steps."
            )

            coverage_after_resume = (
                get_coverage_values(
                    graph=resumed_graph,
                    memory=resumed_memory,
                    action_filter=action_filter,
                )
            )

            transitions_after_resume = (
                get_transition_count(
                    resumed_graph
                )
            )

            states_after_resume = len(
                resumed_graph.states
            )

            executed_after_resume = (
                get_executed_action_keys(
                    graph=resumed_graph,
                    memory=resumed_memory,
                )
            )

            print_coverage(
                title="AFTER RESUME",
                coverage=coverage_after_resume,
                graph=resumed_graph,
            )

            # =================================================
            # CORE RESUME INVARIANTS
            # =================================================

            assert (
                transitions_after_resume
                >
                transitions_before_resume
            ), (
                "Resume did not add transitions."
            )

            assert (
                states_after_resume
                >=
                states_before_resume
            ), (
                "Resume unexpectedly lost graph states."
            )

            assert (
                coverage_after_resume[
                    "eligible_explored_actions"
                ]
                >
                coverage_before_save[
                    "eligible_explored_actions"
                ]
            ), (
                "Resume did not increase explored "
                "eligible actions."
            )

            assert (
                coverage_after_resume[
                    "eligible_explored_actions"
                ]
                >
                coverage_before_save[
                    "eligible_explored_actions"
                ]
            ), (
                "Resume did not increase explored "
                "eligible actions."
            )

            assert (
                coverage_after_resume[
                    "eligible_total_actions"
                ]
                >=
                coverage_before_save[
                    "eligible_total_actions"
                ]
            ), (
                "Resume unexpectedly lost known "
                "eligible actions."
            )

            # Historical actions must remain recorded.

            assert (
                executed_before_resume
                .issubset(
                    executed_after_resume
                )
            ), (
                "Resume lost historical executed-action "
                "knowledge."
            )

            # New executed actions must exist.

            newly_executed_actions = (
                executed_after_resume
                -
                executed_before_resume
            )

            assert (
                len(
                    newly_executed_actions
                )
                >
                0
            ), (
                "Resume recorded no new executed actions."
            )

            # Every successful continuation step must represent
            # an action that was not in historical memory before
            # the resume began.

            for step_result in (
                coordinator_result.step_results
            ):

                if not (
                    step_result.execution_success
                ):
                    continue

                source_node = (
                    resumed_graph.get_state(
                        step_result
                        .source_state_id
                    )
                )

                assert source_node is not None

                executed_key = (
                    source_node.state.state_hash,

                    step_result
                    .selected_action
                    .target,
                )

                assert (
                    executed_key
                    not in
                    executed_before_resume
                ), (
                    "Coordinator re-executed an action "
                    "already recorded before resume."
                )

            # =================================================
            # PHASE F
            #
            # SAVE THE CONTINUED SESSION AS V2
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE F: SAVE UPDATED SESSION V2"
            )

            print(
                "======================================"
            )

            updated_at = datetime.now()

            snapshot_v2 = (
                create_session_snapshot(
                    session_id=SESSION_ID,

                    root_state_id=(
                        loaded_snapshot
                        .root_state_id
                    ),

                    graph=resumed_graph,

                    memory=resumed_memory,

                    created_at=(
                        loaded_snapshot
                        .created_at
                    ),

                    updated_at=updated_at,
                )
            )

            saved_path_v2 = repository.save(
                snapshot_v2
            )

            assert saved_path_v2.is_file()

            print(
                "Saved Updated Session:",
                saved_path_v2,
            )

            # =================================================
            # PHASE G
            #
            # LOAD SESSION V2 AGAIN
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "PHASE G: LOAD UPDATED SESSION V2"
            )

            print(
                "======================================"
            )

            final_snapshot = (
                repository.load(
                    SESSION_ID
                )
            )

            final_graph = (
                final_snapshot.graph
            )

            final_memory = (
                final_snapshot.memory
            )

            # Another genuine reconstruction boundary.

            assert (
                final_graph
                is not resumed_graph
            )

            assert (
                final_memory
                is not resumed_memory
            )

            # =================================================
            # VERIFY CONTINUED KNOWLEDGE SURVIVED SECOND SAVE
            # =================================================

            final_coverage = (
                get_coverage_values(
                    graph=final_graph,
                    memory=final_memory,
                    action_filter=action_filter,
                )
            )

            final_executed_actions = (
                get_executed_action_keys(
                    graph=final_graph,
                    memory=final_memory,
                )
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
                updated_at
            )

            assert (
                len(
                    final_graph.states
                )
                ==
                states_after_resume
            )

            assert (
                get_transition_count(
                    final_graph
                )
                ==
                transitions_after_resume
            )

            assert (
                final_coverage
                ==
                coverage_after_resume
            )

            assert (
                final_executed_actions
                ==
                executed_after_resume
            )

            print_coverage(
                title=(
                    "AFTER SECOND LOAD"
                ),
                coverage=final_coverage,
                graph=final_graph,
            )

            # =================================================
            # FINAL RESULT
            # =================================================

            print()

            print(
                "======================================"
            )

            print(
                "REAL CALCULATOR RESUME VERIFIED"
            )

            print(
                "======================================"
            )

            print(
                "Root State:",
                final_snapshot.root_state_id,
            )

            print(
                "Transitions Before Resume:",
                transitions_before_resume,
            )

            print(
                "Transitions After Resume:",
                transitions_after_resume,
            )

            print(
                "Explored Eligible Before:",
                coverage_before_save[
                    "eligible_explored_actions"
                ],
            )

            print(
                "Explored Eligible After:",
                coverage_after_resume[
                    "eligible_explored_actions"
                ],
            )

            print(
                "Coverage Before:",
                coverage_before_save[
                    "eligible_action_coverage_percentage"
                ],
            )

            print(
                "Coverage After:",
                coverage_after_resume[
                    "eligible_action_coverage_percentage"
                ],
            )

            print(
                "New Executed Actions:",
                len(
                    newly_executed_actions
                ),
            )

            print(
                "Second Save/Load Preserved Resume:",
                final_coverage
                ==
                coverage_after_resume,
            )

            print()

            print(
                "CALCULATOR SESSION RESUME "
                "TEST PASSED"
            )

    finally:

        # Keep the integration environment repeatable.
        #
        # This removes only the known session created by this
        # specific test.

        if session_directory.exists():

            shutil.rmtree(
                session_directory
            )


if __name__ == "__main__":

    test_calculator_session_resume()