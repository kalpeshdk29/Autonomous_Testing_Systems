"""
Verify action discovery.
"""

from tests.fixtures.calculator_fixture import (
    get_calculator
)


def test_action_discovery():

    ui, window = get_calculator()

    state = ui.capture_state(
        window
    )

    assert (
        len(
            state.available_actions
        ) > 0
    )

    print()

    print("ACTIONS")

    for action in (
        state.available_actions
    ):

        print(action)

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_action_discovery()