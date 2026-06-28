"""
Verify action execution.
"""

from tests.fixtures.calculator_fixture import (
    get_calculator
)

from agent.executor.action_executor import (
    ActionExecutor
)


def test_action_execution():

    ui, window = get_calculator()

    state = ui.capture_state(
        window
    )

    action = next(
        a
        for a in state.available_actions
        if a.target == "num7Button"
    )

    executor = ActionExecutor()

    success = executor.execute(
        window,
        action
    )

    assert success

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_action_execution()