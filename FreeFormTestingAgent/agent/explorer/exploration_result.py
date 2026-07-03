"""
File: exploration_result.py

Purpose:
    Stores exploration statistics.
"""

from dataclasses import dataclass


@dataclass
class ExplorationResult:
    """
    Final exploration result.
    """

    states: int

    transitions: int

    actions: int

    duration: float