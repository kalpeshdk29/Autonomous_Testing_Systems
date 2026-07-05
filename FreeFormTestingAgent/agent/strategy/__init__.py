"""
Exploration strategy package.

This package contains the deterministic target-selection layer used to decide
which previously discovered application state should be explored next.

The package deliberately separates:

1. Coverage facts
2. Execution constraints
3. Candidate ranking
4. Final target selection
"""

from agent.strategy.exploration_target import ExplorationTarget
from agent.strategy.exploration_strategy import ExplorationStrategy
from agent.strategy.shallowest_first_strategy import ShallowestFirstStrategy
from agent.strategy.exploration_target_selector import ExplorationTargetSelector

__all__ = [
    "ExplorationTarget",
    "ExplorationStrategy",
    "ShallowestFirstStrategy",
    "ExplorationTargetSelector",
]