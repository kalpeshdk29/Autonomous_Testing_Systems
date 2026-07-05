"""
File:
    test_calculator_exploration_target_selector.py

Purpose:
    Verify that the Exploration Target Selection layer works
    with a real replay-aware Calculator exploration session.

Integration Flow:

    Real Calculator
            ↓
    Replay-Aware BFSExplorer
            ↓
    StateGraph + ExplorationMemory
            ↓
    CoverageEngine
            ↓
    States With Remaining Eligible Actions
            ↓
    ExplorationTargetSelector
            ↓
    ShallowestFirstStrategy
            ↓
    Ranked ExplorationTargets
            ↓
    Best Next Target

What This Test Proves:

    1. Real Calculator exploration creates graph knowledge.

    2. CoverageEngine identifies states containing remaining
       eligible work.

    3. Fully explored states do not become candidates.

    4. States at max_depth do not become candidates.

    5. Valid shallower states remain available for exploration.

    6. The strategy ranks real candidates deterministically.

    7. The selector returns the best next exploration target.
"""

from tests.fixtures.calculator_fixture import (
    CalculatorFixture,
)

from agent.executor.action_executor import (
    ActionExecutor,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
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

from agent.replay.replay_engine import (
    ReplayEngine,
)

from agent.coverage.coverage_engine import (
    CoverageEngine,
)

from agent.strategy.exploration_target_selector import (
    ExplorationTargetSelector,
)

from agent.strategy.shallowest_first_strategy import (
    ShallowestFirstStrategy,
)

from core.graph.state_graph import (
    StateGraph,
)


class TargetSelectionTestActionFilter(
    ActionFilter
):
    """
    Controlled Calculator action policy.

    Only four actions are eligible:

        7
        8
        +
        =

    This is intentionally identical to the existing Calculator
    coverage integration test so the resulting exploration
    behavior remains controlled and inspectable.
    """

    ALLOWED_ACTIONS = {
        "num7Button",
        "num8Button",
        "plusButton",
        "equalButton",
    }

    def allow(
        self,
        action,
    ) -> bool:
        """
        Return True only for controlled Calculator actions.
        """

        return (
            action.target
            in
            self.ALLOWED_ACTIONS
        )


def print_remaining_coverage_states(
    remaining_states,
) -> None:
    """
    Print all states that CoverageEngine reports as having
    remaining eligible work.

    This list may include depth-2 states because CoverageEngine
    reports facts without applying exploration constraints.
    """

    print()
    print(
        "======================================"
    )
    print(
        "COVERAGE ENGINE: REMAINING WORK"
    )
    print(
        "======================================"
    )

    for coverage in remaining_states:

        print(
            coverage.state_id,
            "| Depth:",
            coverage.depth,
            "| Remaining:",
            coverage.eligible_unexplored_actions,
        )


def print_ranked_targets(
    ranked_targets,
) -> None:
    """
    Print the final ranked exploration candidates.
    """

    print()
    print(
        "======================================"
    )
    print(
        "RANKED EXPLORATION TARGETS"
    )
    print(
        "======================================"
    )

    for index, target in enumerate(
        ranked_targets,
        start=1,
    ):

        print(
            index,
            "| State:",
            target.state_id,
            "| Depth:",
            target.depth,
            "| Remaining:",
            target.unexplored_eligible_actions,
        )


def test_calculator_exploration_target_selector():
    """
    Run real Calculator exploration and verify target selection.
    """

    max_depth = 2

    with CalculatorFixture() as (
        ui,
        window,
    ):

        # =====================================================
        # STEP 1
        # Create shared deterministic exploration components
        # =====================================================

        graph = StateGraph()

        memory = ExplorationMemory()

        executor = ActionExecutor()

        action_filter = (
            TargetSelectionTestActionFilter()
        )

        replay_engine = ReplayEngine(
            ui,
            executor,
            graph,
        )

        limits = ExplorationLimits(
            max_states=20,
            max_actions=12,
            max_transitions=20,
            max_depth=max_depth,
            max_duration=120.0,
            max_failures=10,
        )

        # =====================================================
        # STEP 2
        # Create replay-aware BFS explorer
        # =====================================================

        explorer = BFSExplorer(
            ui=ui,
            executor=executor,
            graph=graph,
            memory=memory,
            replay_engine=replay_engine,
            executable="calc.exe",
            window_title="Calculator",
            action_filter=action_filter,
            limits=limits,
        )

        # =====================================================
        # STEP 3
        # Explore the real Calculator
        # =====================================================

        result = explorer.explore(
            window
        )

        print()
        print(
            "===== EXPLORATION RESULT ====="
        )

        print(
            result
        )

        # =====================================================
        # STEP 4
        # Create real CoverageEngine
        # =====================================================

        coverage_engine = CoverageEngine(
            graph=graph,
            memory=memory,
            action_filter=action_filter,
        )

        report = (
            coverage_engine.calculate_report()
        )

        assert report.total_states > 0, (
            "Real exploration created no states."
        )

        # =====================================================
        # STEP 5
        # Get factual remaining work from CoverageEngine
        # =====================================================

        remaining_states = (
            coverage_engine
            .get_states_with_unexplored_eligible_actions()
        )

        print_remaining_coverage_states(
            remaining_states
        )

        assert len(remaining_states) > 0, (
            "CoverageEngine found no remaining eligible work."
        )

        # =====================================================
        # STEP 6
        # Verify CoverageEngine still reports depth-2 work
        #
        # This proves that coverage reports facts independently
        # of exploration constraints.
        # =====================================================

        depth_limit_states = [
            coverage
            for coverage in remaining_states
            if coverage.depth == max_depth
        ]

        assert len(depth_limit_states) > 0, (
            "Expected real depth-2 states with remaining "
            "eligible actions."
        )

        # =====================================================
        # STEP 7
        # Create selector and deterministic strategy
        # =====================================================

        strategy = ShallowestFirstStrategy()

        selector = ExplorationTargetSelector(
            coverage_engine=coverage_engine,
            strategy=strategy,
            max_depth=max_depth,
        )

        # =====================================================
        # STEP 8
        # Get valid candidates
        # =====================================================

        candidates = selector.get_candidates()

        print()
        print(
            "======================================"
        )
        print(
            "VALID EXPLORATION CANDIDATES"
        )
        print(
            "======================================"
        )

        for candidate in candidates:

            print(
                candidate.state_id,
                "| Depth:",
                candidate.depth,
                "| Remaining:",
                candidate.unexplored_eligible_actions,
            )

        assert len(candidates) > 0, (
            "Selector found no valid exploration candidates."
        )

        # =====================================================
        # STEP 9
        # Prove max-depth states were removed
        # =====================================================

        assert all(
            candidate.depth < max_depth
            for candidate in candidates
        ), (
            "Selector included a state that cannot be expanded "
            "under max_depth."
        )

        # =====================================================
        # STEP 10
        # Prove every candidate has remaining eligible work
        # =====================================================

        assert all(
            candidate.unexplored_eligible_actions > 0
            for candidate in candidates
        ), (
            "Selector included a fully eligible-explored state."
        )

        # =====================================================
        # STEP 11
        # Prove the expected valid depth-1 work exists
        # =====================================================

        depth_one_candidates = [
            candidate
            for candidate in candidates
            if candidate.depth == 1
        ]

        assert len(depth_one_candidates) > 0, (
            "Expected remaining valid depth-1 exploration "
            "targets."
        )

        # =====================================================
        # STEP 12
        # Rank real candidates
        # =====================================================

        ranked_targets = (
            selector.rank_targets()
        )

        print_ranked_targets(
            ranked_targets
        )

        assert len(ranked_targets) == len(
            candidates
        ), (
            "Ranking changed the number of candidates."
        )

        # =====================================================
        # STEP 13
        # Verify deterministic ranking order
        # =====================================================

        expected_ranking = sorted(
            candidates,
            key=lambda target: (
                target.depth,
                -target.unexplored_eligible_actions,
                target.state_id,
            ),
        )

        assert ranked_targets == expected_ranking, (
            "Real targets were not ranked according to the "
            "ShallowestFirstStrategy rules."
        )

        # =====================================================
        # STEP 14
        # Select best next target
        # =====================================================

        selected_target = (
            selector.select_next_target()
        )

        assert selected_target is not None, (
            "Selector failed to choose a next target."
        )

        assert (
            selected_target
            ==
            ranked_targets[0]
        ), (
            "Selected target is not the highest-ranked target."
        )

        # =====================================================
        # STEP 15
        # Print final decision
        # =====================================================

        print()
        print(
            "======================================"
        )
        print(
            "SELECTED NEXT EXPLORATION TARGET"
        )
        print(
            "======================================"
        )

        print(
            "State:",
            selected_target.state_id
        )

        print(
            "Depth:",
            selected_target.depth
        )

        print(
            "Remaining Eligible Actions:",
            selected_target.unexplored_eligible_actions
        )

        print(
            "Reason:",
            selected_target.selection_reason
        )

        print()
        print(
            "CALCULATOR EXPLORATION TARGET "
            "SELECTOR TEST PASSED"
        )


if __name__ == "__main__":

    test_calculator_exploration_target_selector()