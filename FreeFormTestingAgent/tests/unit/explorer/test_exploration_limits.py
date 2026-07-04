"""
File: test_exploration_limits.py

Purpose:
    Verify ExplorationLimits configuration.
"""

from agent.explorer.exploration_limits import (
    ExplorationLimits
)


def test_default_exploration_limits():
    """
    Verify default safety limits.
    """

    limits = ExplorationLimits()

    assert limits.max_states == 100

    assert limits.max_actions == 500

    assert limits.max_transitions == 500

    assert limits.max_duration == 300.0

    assert limits.max_failures == 20

    print()
    print(
        "DEFAULT EXPLORATION LIMITS TEST PASSED"
    )


def test_custom_exploration_limits():
    """
    Verify caller-defined limits.
    """

    limits = ExplorationLimits(
    max_states=10,
    max_actions=20,
    max_transitions=30,
    max_depth=3,
    max_duration=60.0,
    max_failures=5
)


    assert limits.max_states == 10

    assert limits.max_actions == 20

    assert limits.max_transitions == 30

    assert limits.max_duration == 60.0

    assert limits.max_failures == 5

    assert limits.max_depth == 3

    print()
    print(
        "CUSTOM EXPLORATION LIMITS TEST PASSED"
    )


if __name__ == "__main__":

    test_default_exploration_limits()

    test_custom_exploration_limits()