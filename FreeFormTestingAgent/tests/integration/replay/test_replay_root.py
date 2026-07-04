"""
File: test_replay_root.py

Purpose:
    Verify that ReplayEngine can restore the root state
    when the source state and target state are the same.

Test Scenario:

    Capture S0
        ↓
    Mutate application:
        S0 --7--> S1
        ↓
    Request replay:
        S0 → S0
        ↓
    Restart application
        ↓
    Execute zero transitions
        ↓
    Verify fresh state == original S0

Why This Test Matters:
    Replay-aware exploration will frequently need to restore
    the root state before testing another branch.

    For example:

        Restore S0 → Execute 7
        Restore S0 → Execute 8
        Restore S0 → Execute 9

    Therefore, root-to-root replay must work reliably.
"""

from tests.fixtures.calculator_fixture import (
    CalculatorFixture
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


def test_replay_root():
    """
    Verify root-to-root replay.

    Expected behavior:

        source_state == target_state

    Therefore:

        transition_path == []

    ReplayEngine should still:

        1. Restart the application.
        2. Execute zero actions.
        3. Capture the fresh state.
        4. Verify it against the original root state.
    """

    with CalculatorFixture() as (
        ui,
        window
    ):

        # =====================================================
        # STEP 1
        # Create test dependencies
        # =====================================================

        graph = StateGraph()

        executor = ActionExecutor()

        # =====================================================
        # STEP 2
        # Capture original root state S0
        # =====================================================

        root_state = ui.capture_state(
            window
        )

        root_state.state_hash = (
            create_state_hash(
                root_state
            )
        )

        root_id = graph.add_state(
            root_state
        )

        print()
        print(
            "Root State:",
            root_id
        )

        print(
            "Root Hash:",
            root_state.state_hash
        )

        # =====================================================
        # STEP 3
        # Verify root-to-root graph path
        # =====================================================

        transition_path = (
            graph.find_transition_path(
                root_id,
                root_id
            )
        )

        assert transition_path is not None, (
            "Root-to-root path should exist."
        )

        assert len(transition_path) == 0, (
            "Root-to-root path should contain "
            "zero transitions."
        )

        print()
        print(
            "Root-to-root transition path:",
            transition_path
        )

        # =====================================================
        # STEP 4
        # Mutate the real application
        # =====================================================

        action7 = next(
            (
                action
                for action
                in root_state.available_actions
                if action.target == "num7Button"
            ),
            None
        )

        assert action7 is not None, (
            "num7Button action was not found."
        )

        print()
        print(
            "Mutating application:"
        )

        success = executor.execute(
            window,
            action7
        )

        assert success, (
            "Failed to mutate Calculator state."
        )

        # =====================================================
        # STEP 5
        # Confirm application is no longer at root
        # =====================================================

        mutated_state = ui.capture_state(
            window
        )

        mutated_state.state_hash = (
            create_state_hash(
                mutated_state
            )
        )

        print()
        print(
            "Mutated Hash:",
            mutated_state.state_hash
        )

        assert (
            mutated_state.state_hash
            != root_state.state_hash
        ), (
            "Calculator did not leave the root state."
        )

        # =====================================================
        # STEP 6
        # Replay S0 → S0
        # =====================================================

        replay_engine = ReplayEngine(
            ui,
            executor,
            graph
        )

        replayed_window = (
            replay_engine.replay(
                executable="calc.exe",
                window_title="Calculator",
                source_state=root_id,
                target_state=root_id
            )
        )

        # =====================================================
        # STEP 7
        # Verify replay succeeded
        # =====================================================

        assert replayed_window is not None, (
            "Root-to-root replay failed."
        )

        print()
        print(
            "ROOT-TO-ROOT REPLAY TEST PASSED"
        )


if __name__ == "__main__":

    test_replay_root()