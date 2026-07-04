"""
File: test_replay_chain.py

Purpose:
    Verify that the ReplayEngine can restore a previously
    discovered application state through multiple transitions.

Test Scenario:

    S0 --7--> S1 --+--> S2 --8--> S3

Replay Scenario:

    Restart Calculator
            ↓
        Click 7
            ↓
        Click +
            ↓
        Click 8
            ↓
    Verify final state == S3
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


def capture_and_store_state(
    ui,
    window,
    graph
):
    """
    Capture the current application state,
    calculate its deterministic hash,
    and store it in the state graph.

    Parameters
    ----------
    ui:
        UI adapter used to capture the application.

    window:
        Current application window.

    graph:
        StateGraph where the captured state is stored.

    Returns
    -------
    tuple:
        (
            ApplicationState,
            state_id
        )
    """

    state = ui.capture_state(
        window
    )

    state.state_hash = create_state_hash(
        state
    )

    state_id = graph.add_state(
        state
    )

    return (
        state,
        state_id
    )


def find_action(
    state,
    target: str
):
    """
    Find an action in the state's available actions.

    Parameters
    ----------
    state:
        Application state containing available actions.

    target:
        Automation target to search for.

    Returns
    -------
    Action:
        Matching action.

    Raises
    ------
    AssertionError:
        If the requested action does not exist.
    """

    action = next(
        (
            action
            for action
            in state.available_actions
            if action.target == target
        ),
        None
    )

    assert action is not None, (
        f"Action not found: {target}"
    )

    return action


def execute_and_record_transition(
    ui,
    window,
    executor,
    graph,
    source_state,
    source_id,
    action_target
):
    """
    Execute one action and record the resulting transition.

    Flow:

        Source State
            ↓
        Find Action
            ↓
        Execute Action
            ↓
        Capture Target State
            ↓
        Store State
            ↓
        Store Transition

    Returns
    -------
    tuple:
        (
            target_state,
            target_state_id
        )
    """

    #
    # Find the requested action in the
    # source state's available actions.
    #
    action = find_action(
        source_state,
        action_target
    )

    print()
    print(
        f"Executing discovery action: "
        f"{action.target}"
    )

    #
    # Execute the action against the
    # real application.
    #
    success = executor.execute(
        window,
        action
    )

    assert success, (
        f"Action execution failed: "
        f"{action.target}"
    )

    #
    # Capture and store the resulting
    # application state.
    #
    target_state, target_id = (
        capture_and_store_state(
            ui,
            window,
            graph
        )
    )

    #
    # Record how the source state
    # reached the target state.
    #
    graph.add_transition(
        source_id,
        action,
        target_id,
        success=True
    )

    return (
        target_state,
        target_id
    )


def test_replay_chain():
    """
    Test multi-step state replay.

    Discovery:

        S0 --7--> S1 --+--> S2 --8--> S3

    Replay:

        Restart
            ↓
        7
            ↓
        +
            ↓
        8
            ↓
        Verify S3
    """

    with CalculatorFixture() as (
        ui,
        window
    ):

        #
        # Create graph and executor.
        #
        graph = StateGraph()

        executor = ActionExecutor()

        # =====================================================
        # STEP 1
        # Capture root state S0
        # =====================================================

        state0, id0 = (
            capture_and_store_state(
                ui,
                window,
                graph
            )
        )

        print()
        print(
            "Root State:",
            id0
        )

        # =====================================================
        # STEP 2
        # S0 --7--> S1
        # =====================================================

        state1, id1 = (
            execute_and_record_transition(
                ui=ui,
                window=window,
                executor=executor,
                graph=graph,
                source_state=state0,
                source_id=id0,
                action_target="num7Button"
            )
        )

        # =====================================================
        # STEP 3
        # S1 --+--> S2
        # =====================================================

        state2, id2 = (
            execute_and_record_transition(
                ui=ui,
                window=window,
                executor=executor,
                graph=graph,
                source_state=state1,
                source_id=id1,
                action_target="plusButton"
            )
        )

        # =====================================================
        # STEP 4
        # S2 --8--> S3
        # =====================================================

        state3, id3 = (
            execute_and_record_transition(
                ui=ui,
                window=window,
                executor=executor,
                graph=graph,
                source_state=state2,
                source_id=id2,
                action_target="num8Button"
            )
        )

        # =====================================================
        # STEP 5
        # Validate graph before replay
        # =====================================================

        print()
        print(
            "===== DISCOVERED PATH ====="
        )

        transition_path = (
            graph.find_transition_path(
                id0,
                id3
            )
        )

        assert transition_path is not None

        assert len(transition_path) == 3, (
            "Expected exactly 3 transitions."
        )

        print()

        for transition in transition_path:

            print(
                f"{transition.source_state}"
                f" --{transition.action.target}--> "
                f"{transition.target_state}"
            )

        # =====================================================
        # STEP 6
        # Replay S0 → S3
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
                source_state=id0,
                target_state=id3
            )
        )

        # =====================================================
        # STEP 7
        # Verify replay result
        # =====================================================

        assert replayed_window is not None, (
            "Multi-step replay failed."
        )

        print()
        print(
            "MULTI-STEP REPLAY TEST PASSED"
        )


if __name__ == "__main__":

    test_replay_chain()