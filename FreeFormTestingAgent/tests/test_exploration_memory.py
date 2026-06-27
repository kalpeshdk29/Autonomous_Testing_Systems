"""
Test ExplorationMemory.
"""

from agent.memory.exploration_memory import (
    ExplorationMemory
)

memory = ExplorationMemory()

state = "state1"

memory.mark_executed(
    state,
    "num7Button"
)

print(
    memory.is_executed(
        state,
        "num7Button"
    )
)

print(
    memory.is_executed(
        state,
        "plusButton"
    )
)