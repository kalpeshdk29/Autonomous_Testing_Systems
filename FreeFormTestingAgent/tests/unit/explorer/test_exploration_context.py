"""
Test ExplorationContext.
"""

from agent.explorer.exploration_context import (
    ExplorationContext
)


def test_exploration_context():

    context = (
        ExplorationContext()
    )

    context.enqueue(
        "S0"
    )

    context.enqueue(
        "S1"
    )

    assert (
        context.has_states()
    )

    assert (
        context.dequeue()
        ==
        "S0"
    )

    assert (
        context.dequeue()
        ==
        "S1"
    )

    print()
    print(
        "TEST PASSED"
    )


if __name__ == "__main__":
    test_exploration_context()