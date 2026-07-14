"""
Represents:

State A
    +
Action
    =
State B
"""

from dataclasses import dataclass
from typing import Any
from typing import Optional


@dataclass
class Transition:

    #
    # Graph structure
    #
    source_state: str
    target_state: str

    #
    # Action executed
    #
    action: Any

    #
    # Execution result
    #
    success: bool = True

    duration: float = 0.0

    #
    # Failure metadata
    #
    failure_reason: Optional[str] = None

    failure_type: Optional[str] = None