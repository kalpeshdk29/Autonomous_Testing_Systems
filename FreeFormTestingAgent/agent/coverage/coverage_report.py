"""
File: coverage_report.py

Purpose:
    Stores global raw and eligible coverage information
    for the known application state graph.

Architecture:

StateCoverage[]
        ↓
CoverageReport
        ↓
Exploration Strategy / AI Planner / Reporting
"""

from dataclasses import dataclass
from dataclasses import field

from agent.coverage.state_coverage import (
    StateCoverage
)


@dataclass
class CoverageReport:
    """
    Global exploration coverage report.

    Raw metrics:
        Include every discovered UI action.

    Eligible metrics:
        Include only actions allowed by the current
        exploration policy.
    """

    total_states: int

    # =====================================================
    # Raw action coverage
    # =====================================================

    total_actions: int

    explored_actions: int

    unexplored_actions: int

    action_coverage_percentage: float

    fully_explored_states: int

    partially_explored_states: int

    unexplored_states: int

    # =====================================================
    # Eligible action coverage
    # =====================================================

    eligible_total_actions: int

    eligible_explored_actions: int

    eligible_unexplored_actions: int

    eligible_action_coverage_percentage: float

    fully_eligible_explored_states: int

    partially_eligible_explored_states: int

    eligible_unexplored_states: int

    # =====================================================
    # Per-state details
    # =====================================================

    state_coverage: list[
        StateCoverage
    ] = field(
        default_factory=list
    )