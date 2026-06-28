"""
Verify exploration memory.
"""

from agent.memory.exploration_memory import (
    ExplorationMemory
)


def test_exploration_memory():

    memory = (
        ExplorationMemory()
    )

    memory.mark_executed(
        "state1",
        "num7Button"
    )

    assert memory.is_executed(
        "state1",
        "num7Button"
    )

    assert not memory.is_executed(
        "state1",
        "plusButton"
    )

    print()
    print("TEST PASSED")


if __name__ == "__main__":
    test_exploration_memory()