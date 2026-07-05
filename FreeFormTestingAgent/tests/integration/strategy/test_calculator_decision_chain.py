"""
File:
    test_calculator_decision_chain.py

Purpose:
    Verify the complete deterministic decision chain using
    a real Windows Calculator exploration session.

Integration Flow:

    Real Calculator
            ↓
    Replay-Aware BFSExplorer
            ↓
    StateGraph + ExplorationMemory
            ↓
    CoverageEngine
            ↓
    ExplorationTargetSelector
            ↓
    Selected Real State
            ↓
    StateGraph.get_state(...)
            ↓
    StateNode.state
            ↓
    ApplicationState.available_actions
            ↓
    ActionSelector
            ↓
    Ranked Real Actions
            ↓
    Selected Next Action

What This Test Proves:

    1. Real Calculator exploration creates remaining work.

    2. ExplorationTargetSelector selects a real expandable
       graph state.

    3. The selected target can be resolved through StateGraph.

    4. The underlying ApplicationState is accessible through
       StateNode.state.

    5. Real available actions can be read from the selected
       application state.

    6. Already executed actions are excluded by
       ExplorationMemory.

    7. Blocked actions are excluded by ActionFilter.

    8. Valid actions are ranked deterministically.

    9. A real next action can be selected.

This test does NOT execute the selected action.

Action execution belongs to the next milestone:

    Single Exploration Step
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

from agent.strategy.action.action_selector import (
    ActionSelector,
)

from agent.strategy.action.deterministic_action_strategy import (
    DeterministicActionStrategy,
)

from core.graph.state_graph import (
    StateGraph,
)


class DecisionChainTestActionFilter(
    ActionFilter
):
    """
    Controlled Calculator exploration policy.

    Only four Calculator actions are eligible:

        7
        8
        +
        =

    The same filter instance is shared by:

        BFSExplorer
        CoverageEngine
        ActionSelector

    This guarantees that all three layers use the same
    definition of eligible work.
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


def print_selected_target(
    target,
) -> None:
    """
    Print the state selected for further exploration.
    """

    print()
    print(
        "======================================"
    )

    print(
        "SELECTED EXPLORATION TARGET"
    )

    print(
        "======================================"
    )

    print(
        "State:",
        target.state_id
    )

    print(
        "State Hash:",
        target.state_hash
    )

    print(
        "Depth:",
        target.depth
    )

    print(
        "Remaining Eligible Actions:",
        target.unexplored_eligible_actions
    )

    print(
        "Reason:",
        target.selection_reason
    )


def print_action_candidates(
    candidates,
) -> None:
    """
    Print valid real action candidates.
    """

    print()
    print(
        "======================================"
    )

    print(
        "VALID ACTION CANDIDATES"
    )

    print(
        "======================================"
    )

    for action in candidates:

        print(
            action.action_type.value,
            "| Target:",
            action.target,
            "| Value:",
            action.value,
        )


def print_ranked_actions(
    ranked_actions,
) -> None:
    """
    Print real actions in deterministic ranking order.
    """

    print()
    print(
        "======================================"
    )

    print(
        "RANKED ACTIONS"
    )

    print(
        "======================================"
    )

    for index, action in enumerate(
        ranked_actions,
        start=1,
    ):

        print(
            index,
            "| Type:",
            action.action_type.value,
            "| Target:",
            action.target,
            "| Value:",
            action.value,
        )


def test_calculator_decision_chain():
    """
    Run real Calculator exploration and verify the complete
    deterministic state-selection and action-selection chain.
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
            DecisionChainTestActionFilter()
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

        assert result.states > 0, (
            "Real Calculator exploration created no states."
        )

        # =====================================================
        # STEP 4
        # Create CoverageEngine
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
            "Coverage report contains no states."
        )

        # =====================================================
        # STEP 5
        # Create target-selection layer
        # =====================================================

        target_strategy = (
            ShallowestFirstStrategy()
        )

        target_selector = (
            ExplorationTargetSelector(
                coverage_engine=coverage_engine,
                strategy=target_strategy,
                max_depth=max_depth,
            )
        )

        # =====================================================
        # STEP 6
        # Select the real next exploration state
        # =====================================================

        selected_target = (
            target_selector.select_next_target()
        )

        assert selected_target is not None, (
            "No real exploration target was selected."
        )

        print_selected_target(
            selected_target
        )

        # =====================================================
        # STEP 7
        # Resolve the selected target through StateGraph
        # =====================================================

        target_node = graph.get_state(
            selected_target.state_id
        )

        assert target_node is not None, (
            "Selected target does not exist in StateGraph."
        )

        # =====================================================
        # STEP 8
        # Retrieve the captured ApplicationState
        #
        # StateNode exposes it through:
        #
        #     node.state
        # =====================================================

        application_state = (
            target_node.state
        )

        assert application_state is not None, (
            "Selected StateNode contains no ApplicationState."
        )

        # =====================================================
        # STEP 9
        # Verify state identity
        # =====================================================

        assert (
            application_state.state_id
            ==
            selected_target.state_id
        ), (
            "Selected target state_id does not match the "
            "ApplicationState stored in StateGraph."
        )

        assert (
            application_state.state_hash
            ==
            selected_target.state_hash
        ), (
            "Selected target state_hash does not match the "
            "ApplicationState stored in StateGraph."
        )

        # =====================================================
        # STEP 10
        # Retrieve real available actions
        # =====================================================

        available_actions = (
            application_state.available_actions
        )

        assert len(available_actions) > 0, (
            "Selected real Calculator state contains no "
            "available actions."
        )

        print()
        print(
            "Available Actions:",
            len(available_actions)
        )

        # =====================================================
        # STEP 11
        # Create action-selection layer
        # =====================================================

        action_strategy = (
            DeterministicActionStrategy()
        )

        action_selector = ActionSelector(
            memory=memory,
            action_filter=action_filter,
            strategy=action_strategy,
        )

        # =====================================================
        # STEP 12
        # Build expected valid actions independently
        #
        # This is intentionally calculated outside ActionSelector.
        #
        # It verifies that ActionSelector correctly combines:
        #
        #     ExplorationMemory
        #         +
        #     ActionFilter
        # =====================================================

        expected_candidates = []

        for action in available_actions:

            already_executed = (
                memory.is_executed(
                    application_state.state_hash,
                    action.target,
                )
            )

            allowed = (
                action_filter.allow(
                    action
                )
            )

            if (
                not already_executed
                and
                allowed
            ):

                expected_candidates.append(
                    action
                )

        # =====================================================
        # STEP 13
        # Get real action candidates
        # =====================================================

        candidates = (
            action_selector.get_candidates(
                state_hash=(
                    application_state.state_hash
                ),
                actions=available_actions,
            )
        )

        print_action_candidates(
            candidates
        )

        assert len(candidates) > 0, (
            "Selected exploration target contains no valid "
            "action candidates."
        )

        # =====================================================
        # STEP 14
        # Verify candidate correctness
        # =====================================================

        expected_targets = {
            action.target
            for action in expected_candidates
        }

        actual_targets = {
            action.target
            for action in candidates
        }

        assert (
            actual_targets
            ==
            expected_targets
        ), (
            "ActionSelector candidates do not match the real "
            "unexplored eligible actions."
        )

        # =====================================================
        # STEP 15
        # Prove every candidate is unexplored
        # =====================================================

        assert all(
            not memory.is_executed(
                application_state.state_hash,
                action.target,
            )
            for action in candidates
        ), (
            "ActionSelector included an already executed action."
        )

        # =====================================================
        # STEP 16
        # Prove every candidate is eligible
        # =====================================================

        assert all(
            action_filter.allow(
                action
            )
            for action in candidates
        ), (
            "ActionSelector included a blocked action."
        )

        # =====================================================
        # STEP 17
        # Verify candidate count matches target metadata
        #
        # ExplorationTarget was created from CoverageEngine.
        #
        # ActionSelector independently derives the valid actions
        # from ApplicationState + Memory + ActionFilter.
        #
        # These two independent views should agree.
        # =====================================================

        assert (
            len(candidates)
            ==
            selected_target.unexplored_eligible_actions
        ), (
            "ExplorationTarget remaining-action count does not "
            "match ActionSelector candidate count."
        )

        # =====================================================
        # STEP 18
        # Rank the real action candidates
        # =====================================================

        ranked_actions = (
            action_selector.rank_actions(
                state_hash=(
                    application_state.state_hash
                ),
                actions=available_actions,
            )
        )

        print_ranked_actions(
            ranked_actions
        )

        assert len(ranked_actions) == len(
            candidates
        ), (
            "Action ranking changed the number of candidates."
        )

        # =====================================================
        # STEP 19
        # Verify deterministic ranking independently
        # =====================================================

        expected_ranking = sorted(
            candidates,
            key=lambda action: (
                action.action_type.value,
                action.target,
                action.value or "",
            ),
        )

        assert (
            ranked_actions
            ==
            expected_ranking
        ), (
            "Real actions were not ranked according to the "
            "DeterministicActionStrategy rules."
        )

        # =====================================================
        # STEP 20
        # Select the real next action
        # =====================================================

        selected_action = (
            action_selector.select_next_action(
                state_hash=(
                    application_state.state_hash
                ),
                actions=available_actions,
            )
        )

        assert selected_action is not None, (
            "ActionSelector failed to select a real action."
        )

        assert (
            selected_action
            ==
            ranked_actions[0]
        ), (
            "Selected action is not the highest-ranked action."
        )

        # =====================================================
        # STEP 21
        # Print final deterministic decision
        # =====================================================

        print()
        print(
            "======================================"
        )

        print(
            "FINAL DETERMINISTIC DECISION"
        )

        print(
            "======================================"
        )

        print(
            "Selected State:",
            selected_target.state_id
        )

        print(
            "State Depth:",
            selected_target.depth
        )

        print(
            "Selected Action:",
            selected_action
        )

        print(
            "Action Target:",
            selected_action.target
        )

        print()
        print(
            "CALCULATOR DECISION CHAIN TEST PASSED"
        )


if __name__ == "__main__":

    test_calculator_decision_chain()