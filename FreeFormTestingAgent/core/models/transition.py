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


@dataclass
class Transition:

    source_state: str
    target_state: str

    action: Any

    success: bool = True

    duration: float = 0.0