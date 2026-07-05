"""
Autonomous exploration coordination package.

The coordinator repeatedly combines:

    Coverage
        ↓
    Target Selection
        ↓
    Single Exploration Step
        ↓
    Updated Graph + Memory
        ↓
    Repeat
"""

from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.coordinator.coordinator_result import (
    CoordinatorResult,
)

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)

from agent.coordinator.exploration_coordinator import (
    ExplorationCoordinator,
)


__all__ = [
    "CoordinatorLimits",
    "CoordinatorResult",
    "CoordinatorStopReason",
    "ExplorationCoordinator",
]