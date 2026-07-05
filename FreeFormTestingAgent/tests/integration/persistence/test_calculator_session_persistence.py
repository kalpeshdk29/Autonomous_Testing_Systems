"""
File:
    test_calculator_session_persistence.py

Purpose:
    Verify that a real Calculator exploration session can be:

        explored
            ↓
        saved to disk
            ↓
        loaded as fresh runtime objects
            ↓
        used to reproduce the same exploration knowledge

Integration Boundary:

    Real Windows Calculator
            ↓
    BFSExplorer
            ↓
    Real StateGraph + ExplorationMemory
            ↓
    ExplorationSessionSnapshot
            ↓
    JsonSessionRepository
            ↓
    session.json
            ↓
    Fresh StateGraph + ExplorationMemory

What This Test Proves:

    1. Real Calculator exploration data is JSON-persistable.

    2. A real session is saved under the existing storage layout.

    3. Root-state identity survives disk persistence.

    4. Real application states survive.

    5. State hashes survive.

    6. Available actions survive.

    7. Transitions and nested Action objects survive.

    8. ExplorationMemory survives.

    9. Graph counts survive.

    10. Coverage is identical before and after disk persistence.

    11. Loaded graph path search still works.

    12. Loaded graph and memory are fresh runtime objects.

Important:
    This test verifies save/load only.

    It intentionally does not resume autonomous exploration.
    Resume behavior belongs to the next integration milestone.
"""

import shutil

from datetime import datetime
from pathlib import Path

from tests.fixtures.calculator_fixture import (
    CalculatorFixture,
)

from agent.coverage.coverage_engine import (
    CoverageEngine,
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

from core.graph.state_graph import (
    StateGraph,
)

from core.models.action import (
    Action,
)

# =============================================================
# TEST CONFIGURATION
# =============================================================


SESSION_ID = "calculator-persistence-integration"

STORAGE_ROOT = Path("storage/database/sessions")


# =============================================================
# CONTROLLED CALCULATOR POLICY
# =============================================================


class CalculatorPersistenceActionFilter(ActionFilter):
    """
    Controlled Calculator exploration policy.

    Only these actions are eligible:

        7
        8
        +
        =

    This is the same small deterministic action space used by
    the earlier Calculator coverage and coordinator tests.
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

        return action.target in self.ALLOWED_ACTIONS


# =============================================================
# HELPERS
# =============================================================


def get_transition_count(
    graph: StateGraph,
) -> int:
    """
    Return the total number of transitions in the graph.
    """

    return sum(len(transitions) for transitions in graph.edges.values())


def get_coverage_values(
    graph: StateGraph,
    memory: ExplorationMemory,
    action_filter: ActionFilter,
) -> dict:
    """
    Return stable aggregate coverage values.

    The exact same action policy is used before and after loading.
    """

    engine = CoverageEngine(
        graph=graph,
        memory=memory,
        action_filter=action_filter,
    )

    report = engine.calculate_report()

    return {
        "total_states": (report.total_states),
        "total_actions": (report.total_actions),
        "explored_actions": (report.explored_actions),
        "unexplored_actions": (report.unexplored_actions),
        "action_coverage_percentage": (report.action_coverage_percentage),
        "eligible_total_actions": (report.eligible_total_actions),
        "eligible_explored_actions": (report.eligible_explored_actions),
        "eligible_unexplored_actions": (report.eligible_unexplored_actions),
        "eligible_action_coverage_percentage": (
            report.eligible_action_coverage_percentage
        ),
    }


def get_state_hashes(
    graph: StateGraph,
) -> set[str]:
    """
    Return all persisted state hashes.
    """

    return {node.state.state_hash for node in graph.states.values()}


def get_available_action_targets(
    graph: StateGraph,
) -> dict[str, list[str]]:
    """
    Return available action targets for every graph state.

    Sorting makes comparison deterministic.
    """

    return {
        state_id: sorted(action.target for action in node.state.available_actions)
        for state_id, node in graph.states.items()
    }


def get_memory_snapshot(
    graph: StateGraph,
    memory: ExplorationMemory,
) -> dict[str, list[str]]:
    """
    Reconstruct observable memory knowledge through the public API.

    For every action discovered in every graph state, record whether
    ExplorationMemory considers that action executed.
    """

    result = {}

    for node in graph.states.values():

        state = node.state

        executed_targets = []

        for action in state.available_actions:

            if memory.is_executed(
                state.state_hash,
                action.target,
            ):

                executed_targets.append(action.target)

        result[state.state_hash] = sorted(executed_targets)

    return result


def find_non_root_reachable_state(
    graph: StateGraph,
    root_state_id: str,
):
    """
    Find one state reachable from the root.

    Returns:
        tuple[target_state_id, path]

    or:
        None
    """

    for state_id in sorted(graph.states.keys()):

        if state_id == root_state_id:
            continue

        path = graph.find_path(
            root_state_id,
            state_id,
        )

        if path is not None:

            return (
                state_id,
                path,
            )

    return None


def print_summary(
    title: str,
    graph: StateGraph,
    memory: ExplorationMemory,
    action_filter: ActionFilter,
):
    """
    Print compact persistence diagnostics.
    """

    coverage = get_coverage_values(
        graph=graph,
        memory=memory,
        action_filter=action_filter,
    )

    print()
    print("======================================")
    print(title)
    print("======================================")

    print(
        "States:",
        len(graph.states),
    )

    print(
        "Transitions:",
        get_transition_count(graph),
    )

    print(
        "Eligible Actions:",
        coverage["eligible_total_actions"],
    )

    print(
        "Explored Eligible Actions:",
        coverage["eligible_explored_actions"],
    )

    print(
        "Unexplored Eligible Actions:",
        coverage["eligible_unexplored_actions"],
    )

    print(
        "Eligible Coverage:",
        coverage["eligible_action_coverage_percentage"],
    )


# =============================================================
# REAL INTEGRATION TEST
# =============================================================


def test_calculator_session_persistence():
    """
    Explore Calculator, persist the complete session, then load
    fresh graph and memory objects and verify equivalent knowledge.
    """

    repository = JsonSessionRepository(storage_root=STORAGE_ROOT)

    session_directory = STORAGE_ROOT / SESSION_ID

    # =========================================================
    # TEST ISOLATION
    #
    # Remove only this integration test's known session folder.
    # Never clear the complete storage directory.
    # =========================================================

    if session_directory.exists():

        shutil.rmtree(session_directory)

    try:

        with CalculatorFixture() as (
            ui,
            window,
        ):

            # =================================================
            # STEP 1
            # Build the real Calculator exploration runtime
            # =================================================

            original_graph = StateGraph()

            original_memory = ExplorationMemory()

            executor = ActionExecutor()

            action_filter = CalculatorPersistenceActionFilter()

            replay_engine = ReplayEngine(
                ui,
                executor,
                original_graph,
            )

            limits = ExplorationLimits(
                max_states=20,
                max_actions=12,
                max_transitions=20,
                max_depth=2,
                max_duration=120.0,
                max_failures=10,
            )

            explorer = BFSExplorer(
                ui=ui,
                executor=executor,
                graph=original_graph,
                memory=original_memory,
                replay_engine=replay_engine,
                executable="calc.exe",
                window_title="Calculator",
                action_filter=action_filter,
                limits=limits,
            )

            # =================================================
            # STEP 2
            # Run real Calculator exploration
            # =================================================

            exploration_result = explorer.explore(window)

            print()
            print("===== INITIAL EXPLORATION RESULT =====")

            print(exploration_result)

            root_state_id = exploration_result.root_state_id

            assert root_state_id is not None, (
                "BFS exploration did not return " "a root_state_id."
            )

            assert original_graph.get_state(root_state_id) is not None, (
                "Exploration root does not exist " "in the original graph."
            )

            assert len(original_graph.states) > 1, (
                "Real Calculator exploration did not " "discover multiple states."
            )

            assert get_transition_count(original_graph) > 0, (
                "Real Calculator exploration created " "no transitions."
            )

            # =================================================
            # STEP 3
            # Capture pre-save knowledge
            # =================================================

            coverage_before = get_coverage_values(
                graph=original_graph,
                memory=original_memory,
                action_filter=action_filter,
            )

            state_hashes_before = get_state_hashes(original_graph)

            actions_before = get_available_action_targets(original_graph)

            memory_before = get_memory_snapshot(
                graph=original_graph,
                memory=original_memory,
            )

            state_count_before = len(original_graph.states)

            transition_count_before = get_transition_count(original_graph)

            reachable_before = find_non_root_reachable_state(
                graph=original_graph,
                root_state_id=root_state_id,
            )

            assert reachable_before is not None, (
                "No graph state is reachable from " "the exploration root."
            )

            print_summary(
                title="BEFORE SAVE",
                graph=original_graph,
                memory=original_memory,
                action_filter=action_filter,
            )

            # =================================================
            # STEP 4
            # Create the durable session snapshot
            # =================================================

            snapshot_time = datetime.now()

            snapshot = ExplorationSessionSnapshot(
                schema_version=(SessionSerializer.CURRENT_SCHEMA_VERSION),
                session_id=SESSION_ID,
                root_state_id=(root_state_id),
                created_at=(snapshot_time),
                updated_at=(snapshot_time),
                graph=original_graph,
                memory=original_memory,
            )

            # =================================================
            # STEP 5
            # Save the real session to project storage
            # =================================================

            saved_path = repository.save(snapshot)

            print()
            print("===== SESSION SAVED =====")

            print(
                "Path:",
                saved_path,
            )

            assert saved_path.is_file()

            assert repository.exists(SESSION_ID)

            assert saved_path == session_directory / "session.json"

            assert not (session_directory / "session.json.tmp").exists()

            # =================================================
            # STEP 6
            # Load fresh runtime objects from disk
            # =================================================

            loaded_snapshot = repository.load(SESSION_ID)

            loaded_graph = loaded_snapshot.graph

            loaded_memory = loaded_snapshot.memory

            # =================================================
            # STEP 7
            # Prove this is a real reconstruction boundary
            # =================================================

            assert loaded_snapshot is not snapshot

            assert loaded_graph is not original_graph

            assert loaded_memory is not original_memory

            # =================================================
            # STEP 8
            # Verify session metadata
            # =================================================

            assert loaded_snapshot.session_id == SESSION_ID

            assert loaded_snapshot.root_state_id == root_state_id

            assert loaded_snapshot.created_at == snapshot.created_at

            assert loaded_snapshot.updated_at == snapshot.updated_at

            assert loaded_graph.get_state(root_state_id) is not None

            # =================================================
            # STEP 9
            # Verify graph knowledge
            # =================================================

            assert len(loaded_graph.states) == state_count_before

            assert get_transition_count(loaded_graph) == transition_count_before

            assert get_state_hashes(loaded_graph) == state_hashes_before

            assert get_available_action_targets(loaded_graph) == actions_before

            # Every loaded transition must still contain a real
            # Action object.

            for transitions in loaded_graph.edges.values():

                for transition in transitions:

                    assert isinstance(
                        transition.action,
                        Action,
                    )

            # =================================================
            # STEP 10
            # Verify ExplorationMemory knowledge
            # =================================================

            memory_after = get_memory_snapshot(
                graph=loaded_graph,
                memory=loaded_memory,
            )

            assert memory_after == memory_before

            assert any(
                executed_targets for executed_targets in memory_after.values()
            ), ("Loaded ExplorationMemory contains " "no executed actions.")

            # =================================================
            # STEP 11
            # Verify exact coverage equivalence
            # =================================================

            coverage_after = get_coverage_values(
                graph=loaded_graph,
                memory=loaded_memory,
                action_filter=action_filter,
            )

            assert coverage_after == coverage_before

            # =================================================
            # STEP 12
            # Verify loaded path search
            # =================================================

            (
                reachable_state_id,
                path_before,
            ) = reachable_before

            path_after = loaded_graph.find_path(
                root_state_id,
                reachable_state_id,
            )

            assert path_after == path_before

            transition_path_after = loaded_graph.find_transition_path(
                root_state_id,
                reachable_state_id,
            )

            assert transition_path_after is not None

            assert len(transition_path_after) == len(path_after) - 1

            print_summary(
                title="AFTER LOAD",
                graph=loaded_graph,
                memory=loaded_memory,
                action_filter=action_filter,
            )

            print()
            print("======================================")
            print("REAL CALCULATOR PERSISTENCE VERIFIED")
            print("======================================")

            print(
                "Session ID:",
                loaded_snapshot.session_id,
            )

            print(
                "Root State:",
                loaded_snapshot.root_state_id,
            )

            print(
                "States:",
                len(loaded_graph.states),
            )

            print(
                "Transitions:",
                get_transition_count(loaded_graph),
            )

            print(
                "Coverage Preserved:",
                coverage_before == coverage_after,
            )

            print()
            print("CALCULATOR SESSION " "PERSISTENCE TEST PASSED")

    finally:

        # =====================================================
        # CLEANUP POLICY
        #
        # Keep this enabled for a repeatable integration test.
        #
        # If you want to inspect the generated real session.json
        # after the first run, temporarily comment out only this
        # cleanup block.
        # =====================================================

        if session_directory.exists():
            pass
            #shutil.rmtree(session_directory)


if __name__ == "__main__":

    test_calculator_session_persistence()
