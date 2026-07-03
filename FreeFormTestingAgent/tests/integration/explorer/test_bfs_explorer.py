"""
Test BFS explorer.
"""

from tests.fixtures.calculator_fixture import (
    CalculatorFixture
)

from adapters.ui.windows_ui import (
    WindowsUIAdapter
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

from core.graph.state_graph import (
    StateGraph
)


def test_bfs_explorer():

    with CalculatorFixture() as (
        ui,
        window
    ):

        graph = StateGraph()

        memory = (
            ExplorationMemory()
        )

        executor = (
            ActionExecutor()
        )

        explorer = (
            BFSExplorer(
                ui,
                executor,
                graph,
                memory
            )
        )

        result = (
            explorer.explore(
                window,
                max_states=10
            )
        )

        print()

        print(result)

        print()

        graph.print_graph()

        assert result.states > 0

        print()
        print(
            "TEST PASSED"
        )


if __name__ == "__main__":
    test_bfs_explorer()