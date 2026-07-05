"""
Structured result of one controlled exploration step.
"""

from dataclasses import dataclass
from typing import Optional

from core.models.action import Action
from core.models.transition import Transition


@dataclass
class ExplorationStepResult:
    """
    Result produced by ExplorationStepExecutor.

    A step may fail at different stages:

        - source state resolution
        - action selection
        - replay
        - action execution

    The result object preserves those outcomes without forcing
    the future coordinator to inspect console output.
    """

    source_state_id: str

    selected_action: Optional[Action] = None

    target_state_id: Optional[str] = None

    transition: Optional[Transition] = None

    replay_success: bool = False

    execution_success: bool = False

    new_state_discovered: bool = False

    duration: float = 0.0

    failure_reason: Optional[str] = None