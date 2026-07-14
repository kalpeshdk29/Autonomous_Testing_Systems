"""
File:
    extract_calculator_knowledge.py

Purpose:
    Extract the complete behavioural knowledge of an application.

Flow

        Launch Application
                ↓
        Initial BFS Discovery
                ↓
        Autonomous Exploration
                ↓
        Complete Behaviour Graph
                ↓
        Persist Session
                ↓
        Export Knowledge

This example demonstrates the complete MVP workflow.
"""

from pathlib import Path
from datetime import datetime

from tests.fixtures.calculator_fixture import (
    CalculatorFixture,
)

from agent.executor.action_executor import (
    ActionExecutor,
)

from agent.explorer.bfs_explorer import (
    BFSExplorer,
)

from agent.explorer.action_filter import (
    ActionFilter,
)

from agent.explorer.exploration_limits import (
    ExplorationLimits,
)

from agent.explorer.exploration_step_executor import (
    ExplorationStepExecutor,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.replay.replay_engine import (
    ReplayEngine,
)

from agent.coverage.coverage_engine import (
    CoverageEngine,
)

from agent.strategy.action.action_selector import (
    ActionSelector,
)

from agent.strategy.action.deterministic_action_strategy import (
    DeterministicActionStrategy,
)

from agent.strategy.exploration_target_selector import (
    ExplorationTargetSelector,
)

from agent.strategy.shallowest_first_strategy import (
    ShallowestFirstStrategy,
)

from agent.coordinator.exploration_coordinator import (
    ExplorationCoordinator,
)

from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)

from agent.persistence.json_session_repository import (
    JsonSessionRepository,
)

from agent.persistence.checkpoint_manager import (
    CheckpointManager,
)

from core.graph.state_graph import (
    StateGraph,
)


# ============================================================
# Configuration
# ============================================================

SESSION_ID = (
    "calculator-knowledge"
)

STORAGE_ROOT = Path(
    "storage/database/sessions"
)


# ============================================================
# Exploration Policy
# ============================================================

class CalculatorActionFilter(
    ActionFilter,
):
    """
    MVP exploration policy.

    Restrict exploration to the calculator
    buttons that are currently supported.
    """

    ALLOWED_ACTIONS = {

        "num0Button",
        "num1Button",
        "num2Button",
        "num3Button",
        "num4Button",
        "num5Button",
        "num6Button",
        "num7Button",
        "num8Button",
        "num9Button",

        "plusButton",
        "minusButton",
        "multiplyButton",
        "divideButton",

        "equalButton",

        "clearButton",
        "clearEntryButton",

        "decimalSeparatorButton",

        "negateButton",

        "backSpaceButton",
    }

    def allow(
        self,
        action,
    ):

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
        )


# ============================================================
# Helpers
# ============================================================

def print_banner(
    title: str,
):

    print()

    print("=" * 70)

    print(title)

    print("=" * 70)

    print()


def print_section(
    title: str,
):

    print()

    print("-" * 70)

    print(title)

    print("-" * 70)

    print()


def transition_count(
    graph,
):

    total = 0

    for transitions in graph.edges.values():

        total += len(transitions)

    return total


def successful_transition_count(
    graph,
):

    total = 0

    for transitions in graph.edges.values():

        for transition in transitions:

            if transition.success:

                total += 1

    return total


def failed_transition_count(
    graph,
):

    total = 0

    for transitions in graph.edges.values():

        for transition in transitions:

            if not transition.success:

                total += 1

    return total


def print_final_summary(
    graph,
    coverage,
    bfs_result,
    coordinator_result,
):

    print_banner(
        "APPLICATION KNOWLEDGE EXTRACTION COMPLETE"
    )

    print(
        f"States                 : {len(graph.states)}"
    )

    print(
        f"Transitions            : {transition_count(graph)}"
    )

    print(
        f"Successful             : {successful_transition_count(graph)}"
    )

    print(
        f"Failed                 : {failed_transition_count(graph)}"
    )

    print()

    print(
        f"Coverage               : "
        f"{coverage.eligible_action_coverage_percentage}%"
    )

    print(
        f"Remaining Actions      : "
        f"{coverage.eligible_unexplored_actions}"
    )

    print()

    print(
        f"BFS Stop               : "
        f"{bfs_result.stop_reason}"
    )

    print(
        f"Coordinator Stop       : "
        f"{coordinator_result.stop_reason}"
    )

    print()

    print(
        "Knowledge extraction finished successfully."
    )