"""
Limits applied to one coordinator continuation run.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class CoordinatorLimits:
    """
    Budget for one autonomous continuation phase.

    These values are continuation-phase limits.

    They do not include work already performed by the initial
    BFS exploration.

    Attributes:
        max_steps:
            Maximum number of single exploration steps attempted.

        max_duration:
            Maximum coordinator runtime in seconds.

        max_failures:
            Maximum number of failed steps allowed.

    None disables the corresponding limit.
    """

    max_steps: int | None = 10

    max_duration: float | None = 120.0

    max_failures: int | None = 5