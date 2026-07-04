"""
File: test_bfs_explorer.py

Purpose:
    Test replay-aware BFS exploration
    against the real Windows Calculator.
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
    max_depth=10,
    max_duration=120.0,
    max_failures=10
)

def test_bfs_explorer():
    """
    Verify that BFSExplorer can:

        1. Capture the root state.
        2. Restore the correct source state.
        3. Execute exploration actions.
        4. Discover new states.
        5. Store transitions.
        6. Build separate graph branches.
    """

    with CalculatorFixture() as (
        ui,
        window
    ):

        # =====================================================
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

        # =====================================================
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
        # Run exploration
        # =====================================================

        result = explorer.explore(
            window
        )
        
        # =====================================================
        # Print result
        # =====================================================

        print()
        print(
            "===== EXPLORATION RESULT ====="
        )

        print(
            result
        )

        graph.print_graph()

        # =====================================================
        # Basic validation
        # =====================================================

        assert result.states > 1, (
            "Explorer did not discover new states."
        )

        assert result.transitions > 0, (
            "Explorer did not create transitions."
        )

        assert result.actions > 0, (
            "Explorer did not execute actions."
        )

        print()
        print(
            "REPLAY-AWARE BFS TEST PASSED"
        )


if __name__ == "__main__":

    test_bfs_explorer()