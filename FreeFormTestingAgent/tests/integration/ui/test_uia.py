"""
Verify UI Automation access.
"""

import uiautomation as auto


def test_uia():

    controls = (
        auto.GetRootControl()
        .GetChildren()
    )

    assert len(controls) > 0

    print()
    print(
        "WINDOWS FOUND:",
        len(controls)
    )

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_uia()