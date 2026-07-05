"""
File:
    test_calculator_exploration_step.py

Purpose:
    Verify one complete exploration step against the real
    Windows Calculator application.

Integration Flow:

    Real Calculator
            ↓
    Initial Replay-Aware BFS Exploration
            ↓
    StateGraph + ExplorationMemory
            ↓
    CoverageEngine
            ↓
    ExplorationTargetSelector
            ↓
    Selected Real Target State
            ↓
    ActionSelector
            ↓
    Selected Real Action
            ↓
    ExplorationStepExecutor
            ↓
    Replay Root → Selected Target
            ↓
    Execute Exactly One Action
            ↓
    Capture Resulting State
            ↓
    Update StateGraph + ExplorationMemory
            ↓
    Recalculate Coverage

What This Test Proves:

    1. BFS exposes the real root state ID.

    2. A real remaining exploration target can be selected.

    3. The target contains a real unexplored eligible action.

    4. ExplorationStepExecutor can replay to the selected state.

    5. Exactly one real action is executed.

    6. The attempted action is recorded in ExplorationMemory.

    7. Exactly one transition is added to StateGraph.

    8. The resulting state exists in StateGraph.

    9. The transition connects the selected source state to the
       resulting target state.

    10. Source-state eligible coverage decreases by exactly one.

This test executes only ONE continuation step after the initial BFS.

It does not implement the autonomous exploration loop.
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

from agent.explorer.exploration_step_executor import (
    ExplorationStepExecutor,
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


class ExplorationStepTestActionFilter(
    ActionFilter
):
    """
    Controlled Calculator action policy.

    Only four Calculator actions are eligible:

        7
        8
        +
        =

    The same filter instance is shared across:

        BFSExplorer
        CoverageEngine
        ActionSelector

    This guarantees a consistent definition of eligible work.
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


def get_transition_count(
    graph,
) -> int:
    """
    Return the total number of transitions currently stored.

    StateGraph stores transitions as:

        source_state_id -> list[Transition]
    """

    return sum(
        len(transitions)
        for transitions in graph.edges.values()
    )


def get_state_coverage(
    coverage_engine,
    state_id,
):
    """
    Return coverage information for one graph state.

    CoverageEngine owns the factual coverage calculation.

    This helper searches the generated report without adding
    coverage logic to the test.
    """

    report = coverage_engine.calculate_report()

    for state_coverage in report.state_coverage:

        if state_coverage.state_id == state_id:

            return state_coverage

    return None


def print_before_step(
    target,
    action,
    state_count,
    transition_count,
    remaining_actions,
) -> None:
    """
    Print the system state immediately before execution.
    """

    print()
    print(
        "======================================"
    )

    print(
        "BEFORE EXPLORATION STEP"
    )

    print(
        "======================================"
    )

    print(
        "Selected State:",
        target.state_id
    )

    print(
        "State Depth:",
        target.depth
    )

    print(
        "Selected Action:",
        action
    )

    print(
        "Action Target:",
        action.target
    )

    print(
        "Source Remaining Eligible Actions:",
        remaining_actions
    )

    print(
        "Graph States:",
        state_count
    )

    print(
        "Graph Transitions:",
        transition_count
    )


def print_step_result(
    result,
) -> None:
    """
    Print the structured ExplorationStepResult.
    """

    print()
    print(
        "======================================"
    )

    print(
        "EXPLORATION STEP RESULT"
    )

    print(
        "======================================"
    )

    print(
        "Source State:",
        result.source_state_id
    )

    print(
        "Selected Action:",
        result.selected_action
    )

    print(
        "Target State:",
        result.target_state_id
    )

    print(
        "Replay Success:",
        result.replay_success
    )

    print(
        "Execution Success:",
        result.execution_success
    )

    print(
        "New State Discovered:",
        result.new_state_discovered
    )

    print(
        "Duration:",
        result.duration
    )

    print(
        "Failure Reason:",
        result.failure_reason
    )


def print_after_step(
    state_count,
    transition_count,
    remaining_actions,
) -> None:
    """
    Print the system state after the step is committed.
    """

    print()
    print(
        "======================================"
    )

    print(
        "AFTER EXPLORATION STEP"
    )

    print(
        "======================================"
    )

    print(
        "Source Remaining Eligible Actions:",
        remaining_actions
    )

    print(
        "Graph States:",
        state_count
    )

    print(
        "Graph Transitions:",
        transition_count
    )


def test_calculator_single_exploration_step():
    """
    Execute one real continuation step after initial Calculator
    exploration and verify all resulting system updates.
    """

    max_depth = 2

    with CalculatorFixture() as (
        ui,
        window,
    ):

        # =====================================================
        # STEP 1
        # Create shared runtime components
        # =====================================================

        graph = StateGraph()

        memory = ExplorationMemory()

        executor = ActionExecutor()

        action_filter = (
            ExplorationStepTestActionFilter()
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
        # Perform initial controlled BFS exploration
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

        exploration_result = explorer.explore(
            window
        )

        print()
        print(
            "===== INITIAL EXPLORATION RESULT ====="
        )

        print(
            exploration_result
        )

        # =====================================================
        # STEP 3
        # Verify explicit root-state metadata
        # =====================================================

        root_state_id = (
            exploration_result.root_state_id
        )

        assert root_state_id is not None, (
            "BFS exploration did not expose root_state_id."
        )

        root_node = graph.get_state(
            root_state_id
        )

        assert root_node is not None, (
            "Exploration root does not exist in StateGraph."
        )

        assert (
            graph.get_state_depth(
                root_state_id
            )
            ==
            0
        ), (
            "Exploration root is not stored at depth 0."
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

        initial_report = (
            coverage_engine.calculate_report()
        )

        assert initial_report.total_states > 0, (
            "Initial coverage report contains no states."
        )

        # =====================================================
        # STEP 5
        # Select a real expandable target state
        # =====================================================

        target_selector = (
            ExplorationTargetSelector(
                coverage_engine=coverage_engine,
                strategy=ShallowestFirstStrategy(),
                max_depth=max_depth,
            )
        )

        selected_target = (
            target_selector.select_next_target()
        )

        assert selected_target is not None, (
            "No exploration target was available."
        )

        # =====================================================
        # STEP 6
        # Resolve the selected source state
        # =====================================================

        source_node = graph.get_state(
            selected_target.state_id
        )

        assert source_node is not None, (
            "Selected exploration target does not exist "
            "in StateGraph."
        )

        source_state = source_node.state

        # =====================================================
        # STEP 7
        # Create real ActionSelector
        # =====================================================

        action_selector = ActionSelector(
            memory=memory,
            action_filter=action_filter,
            strategy=DeterministicActionStrategy(),
        )

        # =====================================================
        # STEP 8
        # Determine the expected action before execution
        #
        # ExplorationStepExecutor will independently ask the
        # same ActionSelector for the next action.
        # =====================================================

        expected_action = (
            action_selector.select_next_action(
                state_hash=source_state.state_hash,
                actions=source_state.available_actions,
            )
        )

        assert expected_action is not None, (
            "Selected target contains no valid next action."
        )

        assert not memory.is_executed(
            source_state.state_hash,
            expected_action.target,
        ), (
            "Expected action was already marked as executed "
            "before the exploration step."
        )

        # =====================================================
        # STEP 9
        # Capture system state before execution
        # =====================================================

        states_before = len(
            graph.states
        )

        transitions_before = (
            get_transition_count(
                graph
            )
        )

        source_coverage_before = (
            get_state_coverage(
                coverage_engine,
                selected_target.state_id,
            )
        )

        assert source_coverage_before is not None, (
            "Selected source state is missing from the "
            "coverage report."
        )

        remaining_before = (
            source_coverage_before
            .eligible_unexplored_actions
        )

        assert remaining_before > 0, (
            "Selected source state has no remaining "
            "eligible work."
        )

        assert (
            remaining_before
            ==
            selected_target.unexplored_eligible_actions
        ), (
            "Selected target metadata does not match current "
            "source-state coverage."
        )

        print_before_step(
            target=selected_target,
            action=expected_action,
            state_count=states_before,
            transition_count=transitions_before,
            remaining_actions=remaining_before,
        )

        # =====================================================
        # STEP 10
        # Create the real single-step executor
        # =====================================================

        step_executor = ExplorationStepExecutor(
            ui=ui,
            executor=executor,
            graph=graph,
            memory=memory,
            replay_engine=replay_engine,
            action_selector=action_selector,
            executable="calc.exe",
            window_title="Calculator",
        )

        # =====================================================
        # STEP 11
        # Execute exactly one real exploration step
        # =====================================================

        step_result = (
            step_executor.execute_step(
                root_state_id=root_state_id,
                source_state_id=(
                    selected_target.state_id
                ),
            )
        )

        print_step_result(
            step_result
        )

        # =====================================================
        # STEP 12
        # Verify replay and execution succeeded
        # =====================================================

        assert step_result.replay_success is True, (
            "Replay to selected Calculator state failed."
        )

        assert step_result.execution_success is True, (
            "Selected Calculator action failed to execute."
        )

        assert step_result.failure_reason is None, (
            "Successful step unexpectedly contains a "
            "failure reason."
        )

        # =====================================================
        # STEP 13
        # Verify the expected action was executed
        # =====================================================

        assert (
            step_result.selected_action
            ==
            expected_action
        ), (
            "ExplorationStepExecutor executed a different "
            "action than ActionSelector selected."
        )

        # =====================================================
        # STEP 14
        # Verify action attempt was recorded
        # =====================================================

        assert memory.is_executed(
            source_state.state_hash,
            expected_action.target,
        ), (
            "Executed action was not recorded in "
            "ExplorationMemory."
        )

        # =====================================================
        # STEP 15
        # Verify resulting target state exists
        # =====================================================

        assert step_result.target_state_id is not None, (
            "Successful step returned no target state."
        )

        resulting_node = graph.get_state(
            step_result.target_state_id
        )

        assert resulting_node is not None, (
            "Resulting Calculator state was not stored "
            "in StateGraph."
        )

        # =====================================================
        # STEP 16
        # Verify exactly one transition was added
        # =====================================================

        transitions_after = (
            get_transition_count(
                graph
            )
        )

        assert (
            transitions_after
            ==
            transitions_before + 1
        ), (
            "Single exploration step did not add exactly "
            "one transition."
        )

        # =====================================================
        # STEP 17
        # Verify the returned transition
        # =====================================================

        transition = step_result.transition

        assert transition is not None, (
            "Successful step returned no transition."
        )

        assert (
            transition.source_state
            ==
            selected_target.state_id
        ), (
            "Transition source does not match the selected "
            "exploration target."
        )

        assert (
            transition.target_state
            ==
            step_result.target_state_id
        ), (
            "Transition target does not match the resulting "
            "state."
        )

        assert (
            transition.action
            ==
            expected_action
        ), (
            "Transition action does not match the selected "
            "action."
        )

        assert transition.success is True, (
            "Successful exploration step stored a failed "
            "transition."
        )

        # =====================================================
        # STEP 18
        # Verify graph state-count behavior
        #
        # A step may:
        #
        #     discover a new state
        #
        # or:
        #
        #     reach an existing state
        #
        # Both are valid.
        # =====================================================

        states_after = len(
            graph.states
        )

        if step_result.new_state_discovered:

            assert (
                states_after
                ==
                states_before + 1
            ), (
                "Step reported a new state but graph state "
                "count did not increase by one."
            )

        else:

            assert (
                states_after
                ==
                states_before
            ), (
                "Step reported an existing state but graph "
                "state count changed."
            )

        # =====================================================
        # STEP 19
        # Recalculate coverage after the step
        # =====================================================

        source_coverage_after = (
            get_state_coverage(
                coverage_engine,
                selected_target.state_id,
            )
        )

        assert source_coverage_after is not None, (
            "Source state disappeared from coverage after "
            "the exploration step."
        )

        remaining_after = (
            source_coverage_after
            .eligible_unexplored_actions
        )

        # =====================================================
        # STEP 20
        # Prove the decision changed coverage
        #
        # Exactly one previously unexplored eligible action
        # was attempted from this source state.
        # =====================================================

        assert (
            remaining_after
            ==
            remaining_before - 1
        ), (
            "Source-state remaining eligible coverage did "
            "not decrease by exactly one."
        )

        print_after_step(
            state_count=states_after,
            transition_count=transitions_after,
            remaining_actions=remaining_after,
        )

        # =====================================================
        # STEP 21
        # Final success output
        # =====================================================

        print()
        print(
            "======================================"
        )

        print(
            "SINGLE EXPLORATION STEP VERIFIED"
        )

        print(
            "======================================"
        )

        print(
            "Root State:",
            root_state_id
        )

        print(
            "Source State:",
            selected_target.state_id
        )

        print(
            "Executed Action:",
            expected_action
        )

        print(
            "Result State:",
            step_result.target_state_id
        )

        print(
            "Remaining Before:",
            remaining_before
        )

        print(
            "Remaining After:",
            remaining_after
        )

        print()
        print(
            "CALCULATOR SINGLE EXPLORATION STEP "
            "TEST PASSED"
        )


if __name__ == "__main__":

    test_calculator_single_exploration_step()