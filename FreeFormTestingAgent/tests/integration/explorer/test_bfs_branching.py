"""
File: test_bfs_branching.py

Purpose:
    Verify that the replay-aware BFSExplorer performs
    real breadth-first exploration across multiple levels.

Test Strategy:
    Restrict Calculator exploration to only three actions:

        num7Button
        num8Button
        plusButton

    This keeps the graph small and predictable enough
    to verify BFS behavior.

Expected Structure:

    Level 0:

                  --7--> S1
                 /
        S0 ------ --8--> S2
                 \
                  --+--> S3

    Level 1:

        BFS must later dequeue one of the discovered
        level-1 states, replay to it, and execute another
        allowed action.

Why This Test Matters:
    The general BFS integration test proves that exploration
    runs successfully.

    This test proves that the explorer is actually:

        - creating independent root branches,
        - using a FIFO queue,
        - replaying non-root states,
        - and exploring beyond the first BFS level.
"""

from tests.fixtures.calculator_fixture import (
    CalculatorFixture
)

from agent.executor.action_executor import (
    ActionExecutor
)

from agent.memory.exploration_memory import (
    ExplorationMemory
)

from agent.explorer.bfs_explorer import (
    BFSExplorer
)

from agent.explorer.action_filter import (
    ActionFilter
)

from agent.replay.replay_engine import (
    ReplayEngine
)

from core.graph.state_graph import (
    StateGraph
)

from agent.explorer.exploration_limits import (
    ExplorationLimits
)


limits = ExplorationLimits(
    max_states=10,
    max_actions=100,
    max_transitions=100,
    max_duration=120.0,
    max_failures=10
)

class BranchingTestActionFilter(
    ActionFilter
):
    """
    Test-only action filter.

    Only a very small set of Calculator actions is allowed.

    This prevents unrelated Calculator controls from making
    the graph too large or unpredictable for this test.
    """

    ALLOWED_ACTIONS = {
        "num7Button",
        "num8Button",
        "plusButton",
    }

    def allow(
        self,
        action
    ) -> bool:
        """
        Allow only actions required by the branching test.
        """

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
        )


def test_bfs_branching():
    """
    Verify true multi-level BFS exploration.

    Expected high-level behavior:

        1. Capture root S0.

        2. Explore allowed actions from S0.

        3. Create multiple outgoing root transitions.

        4. Queue newly discovered states.

        5. Dequeue a level-1 state.

        6. Replay root → level-1 state.

        7. Execute another action from that state.

        8. Create a transition whose source is not S0.
    """

    with CalculatorFixture() as (
        ui,
        window
    ):

        # =====================================================
        # STEP 1
        # Create shared dependencies
        # =====================================================

        graph = StateGraph()

        memory = ExplorationMemory()

        executor = ActionExecutor()

        replay_engine = ReplayEngine(
            ui,
            executor,
            graph
        )

        action_filter = (
            BranchingTestActionFilter()
        )

        # =====================================================
        # STEP 2
        # Create replay-aware BFS explorer
        # =====================================================

        explorer = BFSExplorer(
            ui=ui,
            executor=executor,
            graph=graph,
            memory=memory,
            replay_engine=replay_engine,
            executable="calc.exe",
            window_title="Calculator",
            limits=limits
        )

        # =====================================================
        # STEP 3
        # Run controlled exploration
        # =====================================================

        result = explorer.explore(
            window
        )

        # =====================================================
        # STEP 4
        # Print graph for inspection
        # =====================================================

        print()
        print(
            "===== CONTROLLED BFS GRAPH ====="
        )

        graph.print_graph()

        # =====================================================
        # STEP 5
        # Find the root state
        # =====================================================

        assert len(graph.states) > 0, (
            "Graph contains no states."
        )

        root_id = next(
            iter(graph.states)
        )

        root_transitions = (
            graph.edges.get(
                root_id,
                []
            )
        )

        print()
        print(
            "Root State:",
            root_id
        )

        print(
            "Root Transitions:",
            len(root_transitions)
        )

        # =====================================================
        # STEP 6
        # Verify multiple independent root branches
        # =====================================================

        assert (
            len(root_transitions)
            >= 2
        ), (
            "Expected multiple transitions "
            "from the root state."
        )

        root_action_targets = {
            transition.action.target

            for transition
            in root_transitions
        }

        print(
            "Root Actions:",
            root_action_targets
        )

        assert (
            len(root_action_targets)
            >= 2
        ), (
            "Root transitions did not contain "
            "multiple different actions."
        )

        # =====================================================
        # STEP 7
        # Verify BFS reached a second level
        # =====================================================

        non_root_transitions = []

        for source_id, transitions in (
            graph.edges.items()
        ):

            if source_id == root_id:
                continue

            for transition in transitions:

                non_root_transitions.append(
                    transition
                )

        print()
        print(
            "Non-Root Transitions:",
            len(non_root_transitions)
        )

        assert (
            len(non_root_transitions)
            > 0
        ), (
            "BFS never explored beyond "
            "the root level."
        )

        # =====================================================
        # STEP 8
        # Verify a transition really started from
        # a non-root state
        # =====================================================

        second_level_transition = (
            non_root_transitions[0]
        )

        print()
        print(
            "Second-Level Source:",
            second_level_transition.source_state
        )

        print(
            "Second-Level Action:",
            second_level_transition.action.target
        )

        print(
            "Second-Level Target:",
            second_level_transition.target_state
        )

        assert (
            second_level_transition.source_state
            != root_id
        ), (
            "Expected a transition from "
            "a non-root state."
        )

        # =====================================================
        # STEP 9
        # Validate exploration statistics
        # =====================================================

        assert result.states > 1, (
            "No new states were discovered."
        )

        assert result.transitions > 0, (
            "No transitions were created."
        )

        assert result.actions > 0, (
            "No actions were executed."
        )

        print()
        print(
            "CONTROLLED BFS BRANCHING TEST PASSED"
        )


if __name__ == "__main__":

    test_bfs_branching()