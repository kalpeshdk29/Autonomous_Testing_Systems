"""
File: test_bfs_depth_limit.py

Purpose:
    Verify that replay-aware BFS correctly tracks state depth
    and prevents expansion beyond the configured max_depth.

Test Strategy:
    Restrict Calculator exploration to:

        num7Button
        num8Button
        plusButton

    Configure:

        max_depth = 1

Expected Behavior:

        S0 [depth 0]
        ├── action → S1 [depth 1]
        ├── action → S2 [depth 1]
        └── action → S3 [depth 1]

    Depth-1 states may exist in the graph.

    However:

        Depth-1 states must have no outgoing transitions

    because they are not allowed to expand.
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

from agent.explorer.exploration_limits import (
    ExplorationLimits
)

from agent.replay.replay_engine import (
    ReplayEngine
)

from core.graph.state_graph import (
    StateGraph
)


class DepthTestActionFilter(
    ActionFilter
):
    """
    Allow only a small, controlled set of Calculator actions.
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
        Return True only for actions used by this test.
        """

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
        )


def test_bfs_depth_limit():
    """
    Verify max_depth enforcement.

    Configuration:

        max_depth = 1

    Expected:

        Root:
            depth = 0
            may be expanded

        Children:
            depth = 1
            may be stored
            must not be expanded
    """

    with CalculatorFixture() as (
        ui,
        window
    ):

        # =====================================================
        # STEP 1
        # Create dependencies
        # =====================================================

        graph = StateGraph()

        memory = ExplorationMemory()

        executor = ActionExecutor()

        replay_engine = ReplayEngine(
            ui,
            executor,
            graph
        )

        limits = ExplorationLimits(
            max_states=20,
            max_actions=50,
            max_transitions=50,
            max_depth=1,
            max_duration=120.0,
            max_failures=10
        )

        # =====================================================
        # STEP 2
        # Create controlled explorer
        # =====================================================

        explorer = BFSExplorer(
            ui=ui,
            executor=executor,
            graph=graph,
            memory=memory,
            replay_engine=replay_engine,
            executable="calc.exe",
            window_title="Calculator",
            action_filter=DepthTestActionFilter(),
            limits=limits
        )

        # =====================================================
        # STEP 3
        # Run exploration
        # =====================================================

        result = explorer.explore(
            window
        )

        # =====================================================
        # STEP 4
        # Print graph and depths
        # =====================================================

        print()
        print(
            "===== DEPTH-LIMITED GRAPH ====="
        )

        graph.print_graph()

        print()
        print(
            "===== STATE DEPTHS ====="
        )

        for state_id, node in graph.states.items():

            print(
                state_id,
                "Depth:",
                node.depth
            )

        # =====================================================
        # STEP 5
        # Find the root
        # =====================================================

        root_id = next(
            iter(graph.states)
        )

        root_depth = (
            graph.get_state_depth(
                root_id
            )
        )

        assert root_depth == 0, (
            "Root state must have depth 0."
        )

        # =====================================================
        # STEP 6
        # Root must have been expanded
        # =====================================================

        root_transitions = (
            graph.edges.get(
                root_id,
                []
            )
        )

        assert len(root_transitions) > 0, (
            "Root state was not explored."
        )

        # =====================================================
        # STEP 7
        # No discovered state may exceed max_depth
        # =====================================================

        for state_id, node in graph.states.items():

            assert node.depth <= 1, (
                f"State {state_id} exceeded max_depth. "
                f"Depth: {node.depth}"
            )

        # =====================================================
        # STEP 8
        # Depth-1 states must not be expanded
        # =====================================================

        depth_one_states = [
            state_id

            for state_id, node
            in graph.states.items()

            if node.depth == 1
        ]

        assert len(depth_one_states) > 0, (
            "No depth-1 states were discovered."
        )

        for state_id in depth_one_states:

            outgoing_transitions = (
                graph.edges.get(
                    state_id,
                    []
                )
            )

            assert (
                len(outgoing_transitions)
                == 0
            ), (
                f"Depth-1 state {state_id} "
                f"was incorrectly expanded."
            )

        # =====================================================
        # STEP 9
        # Final validation
        # =====================================================

        assert result.states > 1

        assert result.transitions > 0

        print()
        print(
            "BFS DEPTH LIMIT TEST PASSED"
        )


if __name__ == "__main__":

    test_bfs_depth_limit()
    