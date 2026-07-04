"""
Test replay engine.
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

from agent.replay.replay_engine import (
    ReplayEngine
)

from core.graph.state_graph import (
    StateGraph
)

from core.state.state_hasher import (
    create_state_hash
)


def test_replay_engine():

    with CalculatorFixture() as (
        ui,
        window
    ):

        graph = StateGraph()

        executor = (
            ActionExecutor()
        )

        #
        # Capture root
        #
        state0 = (
            ui.capture_state(
                window
            )
        )

        state0.state_hash = (
            create_state_hash(
                state0
            )
        )

        id0 = (
            graph.add_state(
                state0
            )
        )

        #
        # Click 7
        #
        action7 = next(
            a
            for a in
            state0.available_actions
            if a.target ==
            "num7Button"
        )

        executor.execute(
            window,
            action7
        )

        state1 = (
            ui.capture_state(
                window
            )
        )

        state1.state_hash = (
            create_state_hash(
                state1
            )
        )

        id1 = (
            graph.add_state(
                state1
            )
        )

        graph.add_transition(
            id0,
            action7,
            id1
        )

        #
        # Replay
        #
        replay = (
            ReplayEngine(
                ui,
                executor,
                graph
            )
        )

        replayed_window = replay.replay(
            "calc.exe",
            "Calculator",
            id0,
            id1
        )

        assert replayed_window is not None

        print()
        print(
            "TEST PASSED"
        )


if __name__ == "__main__":
    test_replay_engine()