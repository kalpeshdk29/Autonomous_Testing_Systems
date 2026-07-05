"""
Structured result of one coordinator continuation run.
"""

from dataclasses import dataclass, field

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)

from agent.explorer.exploration_step_result import (
    ExplorationStepResult,
)


@dataclass
class CoordinatorResult:
    """
    Final result of an autonomous continuation run.

    Attributes:
        steps:
            Number of exploration steps attempted.

        successful_steps:
            Number of steps whose action execution succeeded.

        failed_steps:
            Number of steps that failed before producing a
            successful execution result.

        new_states:
            Number of successful steps that discovered a new state.

        duration:
            Total coordinator runtime in seconds.

        stop_reason:
            Reason why the coordinator stopped.

        step_results:
            Ordered history of every attempted step.
    """

    steps: int

    successful_steps: int

    failed_steps: int

    new_states: int

    duration: float

    stop_reason: CoordinatorStopReason

    step_results: list[ExplorationStepResult] = field(
        default_factory=list
    )