"""
File:
    tests/test_state_graph.py

Purpose:
    Verify that StateGraph correctly stores:

        State
            ↓
        Action
            ↓
        State

using the real Windows calculator.
"""

import time

from adapters.ui.windows_ui import WindowsUIAdapter

from agent.executor.action_executor import (
    ActionExecutor
)

from core.graph.state_graph import (
    StateGraph
)

from core.state.state_hasher import (
    create_state_hash
)

from tests.fixtures.calculator_fixture import(
    get_calculator
)


def test_state_graph():

    # ==========================================
    # Setup
    # ==========================================

    ui , window = get_calculator()
    graph = StateGraph()


    # ==========================================
    # Capture initial state
    # ==========================================

    state_before = ui.capture_state(
        window
    )

    state_before.state_hash = (
        create_state_hash(
            state_before
        )
    )

    id_before = graph.add_state(
        state_before
    )

    # ==========================================
    # Find action
    # ==========================================

    action = next(
        a
        for a in state_before.available_actions
        if a.target == "num7Button"
    )

    # ==========================================
    # Execute action
    # ==========================================

    executor = ActionExecutor()

    start = time.time()

    success = executor.execute(
        window,
        action
    )

    duration = (
        time.time()
        - start
    )

    assert success

    # ==========================================
    # Capture new state
    # ==========================================

    state_after = ui.capture_state(
        window
    )

    state_after.state_hash = (
        create_state_hash(
            state_after
        )
    )

    id_after = graph.add_state(
        state_after
    )

    # ==========================================
    # Store transition
    # ==========================================

    graph.add_transition(
        source_id=id_before,
        action=action,
        target_id=id_after,
        success=success,
        duration=duration
    )

    # ==========================================
    # Verify graph
    # ==========================================

    assert len(graph.states) == 2

    assert (
        len(
            graph.edges[id_before]
        )
        == 1
    )

    # ==========================================
    # Verify path finding
    # ==========================================

    path = graph.find_path(
        id_before,
        id_after
    )

    assert path is not None

    assert len(path) == 2

    print()
    print("PATH:")
    print(path)

    print()
    graph.print_graph()

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_state_graph()