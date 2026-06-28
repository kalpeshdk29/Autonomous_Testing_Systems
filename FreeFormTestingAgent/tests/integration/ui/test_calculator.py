"""
Verify calculator controls can be discovered.
"""

from tests.fixtures.calculator_fixture import (
    get_calculator
)


def test_calculator():

    ui, window = get_calculator()

    controls = ui.get_controls(
        window
    )

    assert len(controls) > 0

    print()
    print(
        "TOTAL:",
        len(controls)
    )

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_calculator()