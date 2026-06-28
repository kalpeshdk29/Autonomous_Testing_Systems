"""
Verify calculator values extraction.
"""

from tests.fixtures.calculator_fixture import (
    get_calculator
)


def test_state_values():

    ui, window = get_calculator()

    state = ui.capture_state(
        window
    )

    assert len(state.values) > 0

    print()

    print("VALUES")

    for k, v in state.values.items():

        print(
            k,
            "=",
            v
        )

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_state_values()