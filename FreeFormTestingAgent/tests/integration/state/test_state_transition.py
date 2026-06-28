"""
Verify calculator state transition.
"""

from tests.fixtures.calculator_fixture import (
    get_calculator
)

from agent.executor.action_executor import (
    ActionExecutor
)


def test_state_transition():

    ui, window = get_calculator()

    state_before = (
        ui.capture_state(
            window
        )
    )

    action = next(
        a
        for a in state_before.available_actions
        if a.target == "num7Button"
    )

    executor = ActionExecutor()

    executor.execute(
        window,
        action
    )

    state_after = (
        ui.capture_state(
            window
        )
    )

    assert (
        state_before.values
        !=
        state_after.values
    )

    print()
    print("BEFORE")
    print(state_before.values)

    print()
    print("AFTER")
    print(state_after.values)

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_state_transition()