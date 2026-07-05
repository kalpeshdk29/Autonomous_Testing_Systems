"""
File:
    test_calculator_exploration_coordinator.py

Purpose:
    Verify the autonomous deterministic continuation loop against
    the real Windows Calculator application.

Integration Flow:

    Real Calculator
            ↓
    Initial Controlled BFS Exploration
            ↓
    StateGraph + ExplorationMemory
            ↓
    CoverageEngine
            ↓
    ExplorationTargetSelector
            ↓
    ExplorationCoordinator
            ↓
    ┌─────────────────────────────────────┐
    │ Select Target                       │
    │        ↓                            │
    │ Execute One Exploration Step        │
    │        ↓                            │
    │ Graph + Memory Updated              │
    │        ↓                            │
    │ Coverage Changes                    │
    │        ↓                            │
    │ Select Again                        │
    └─────────────────────────────────────┘
            ↓
    Coordinator Limit Reached

What This Test Proves:

    1. Initial BFS exposes a valid root state.

    2. Real remaining continuation work exists.

    3. ExplorationCoordinator performs multiple autonomous steps.

    4. Target selection is repeated after graph and memory changes.

    5. Every attempted step is preserved in order.

    6. Successful steps update ExplorationMemory.

    7. Successful steps create exactly one transition each.

    8. Newly discovered states are counted correctly.

    9. Source states remain within the configured expansion depth.

    10. Executed eligible coverage increases.

    11. The coordinator stops at its own continuation-step budget.

Important Coverage Semantics:

    Total remaining work does not have to decrease.

    A successful step may:

        consume 1 unexplored action

    while also:

        discovering a new state with several new actions

    Therefore this test verifies actual executed coverage progress,
    not a simplistic decrease in total remaining work.
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

from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)

from agent.coordinator.exploration_coordinator import (
    ExplorationCoordinator,
)

from core.graph.state_graph import (
    StateGraph,
)


class CoordinatorTestActionFilter(
    ActionFilter
):
    """
    Controlled Calculator action policy.

    Only four actions are eligible:

        7
        8
        +
        =

    The same policy is shared across:

        BFSExplorer
        CoverageEngine
        ActionSelector
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
    Return total transitions stored in StateGraph.
    """

    return sum(
        len(transitions)
        for transitions in graph.edges.values()
    )


def get_coverage_totals(
    coverage_engine,
):
    """
    Return aggregate eligible-coverage values using the real
    CoverageReport API.
    """

    report = coverage_engine.calculate_report()

    return {
        "total_states": report.total_states,

        "eligible_actions": (
            report.eligible_total_actions
        ),

        "explored_eligible_actions": (
            report.eligible_explored_actions
        ),

        "unexplored_eligible_actions": (
            report.eligible_unexplored_actions
        ),

        "eligible_coverage_percentage": (
             report.eligible_action_coverage_percentage
        ),
    }


def print_coverage(
    title,
    coverage,
) -> None:
    """
    Print aggregate coverage values.
    """

    print()
    print(
        "======================================"
    )

    print(
        title
    )

    print(
        "======================================"
    )

    print(
        "Total States:",
        coverage["total_states"]
    )

    print(
        "Eligible Actions:",
        coverage["eligible_actions"]
    )

    print(
        "Explored Eligible Actions:",
        coverage["explored_eligible_actions"]
    )

    print(
        "Unexplored Eligible Actions:",
        coverage["unexplored_eligible_actions"]
    )

    print(
        "Eligible Coverage:",
        coverage["eligible_coverage_percentage"]
    )


def print_coordinator_result(
    result,
) -> None:
    """
    Print the autonomous continuation result.
    """

    print()
    print(
        "======================================"
    )

    print(
        "COORDINATOR RESULT"
    )

    print(
        "======================================"
    )

    print(
        "Steps:",
        result.steps
    )

    print(
        "Successful Steps:",
        result.successful_steps
    )

    print(
        "Failed Steps:",
        result.failed_steps
    )

    print(
        "New States:",
        result.new_states
    )

    print(
        "Duration:",
        result.duration
    )

    print(
        "Stop Reason:",
        result.stop_reason
    )


def print_step_history(
    step_results,
) -> None:
    """
    Print every autonomous continuation step in order.
    """

    print()
    print(
        "======================================"
    )

    print(
        "AUTONOMOUS STEP HISTORY"
    )

    print(
        "======================================"
    )

    for index, result in enumerate(
        step_results,
        start=1,
    ):

        print()

        print(
            "Step:",
            index
        )

        print(
            "  Source State:",
            result.source_state_id
        )

        print(
            "  Selected Action:",
            result.selected_action
        )

        print(
            "  Target State:",
            result.target_state_id
        )

        print(
            "  Replay Success:",
            result.replay_success
        )

        print(
            "  Execution Success:",
            result.execution_success
        )

        print(
            "  New State:",
            result.new_state_discovered
        )

        print(
            "  Failure Reason:",
            result.failure_reason
        )


def test_calculator_exploration_coordinator():
    """
    Perform initial Calculator exploration, then autonomously
    continue for exactly three coordinator steps.
    """

    max_depth = 2

    coordinator_max_steps = 3

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
            CoordinatorTestActionFilter()
        )

        replay_engine = ReplayEngine(
            ui,
            executor,
            graph,
        )

        # =====================================================
        # STEP 2
        # Run initial controlled BFS
        # =====================================================

        bfs_limits = ExplorationLimits(
            max_states=20,
            max_actions=12,
            max_transitions=20,
            max_depth=max_depth,
            max_duration=120.0,
            max_failures=10,
        )

        explorer = BFSExplorer(
            ui=ui,
            executor=executor,
            graph=graph,
            memory=memory,
            replay_engine=replay_engine,
            executable="calc.exe",
            window_title="Calculator",
            action_filter=action_filter,
            limits=bfs_limits,
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
        # Verify root-state metadata
        # =====================================================

        root_state_id = (
            exploration_result.root_state_id
        )

        assert root_state_id is not None, (
            "Initial BFS did not expose root_state_id."
        )

        assert graph.get_state(
            root_state_id
        ) is not None, (
            "Root state does not exist in StateGraph."
        )

        assert (
            graph.get_state_depth(
                root_state_id
            )
            ==
            0
        ), (
            "Root state is not stored at depth 0."
        )

        # =====================================================
        # STEP 4
        # Create coverage and target-selection layers
        # =====================================================

        coverage_engine = CoverageEngine(
            graph=graph,
            memory=memory,
            action_filter=action_filter,
        )

        target_selector = (
            ExplorationTargetSelector(
                coverage_engine=coverage_engine,
                strategy=ShallowestFirstStrategy(),
                max_depth=max_depth,
            )
        )

        initial_target = (
            target_selector.select_next_target()
        )

        assert initial_target is not None, (
            "Initial BFS left no continuation work."
        )

        # =====================================================
        # STEP 5
        # Create action-selection layer
        # =====================================================

        action_selector = ActionSelector(
            memory=memory,
            action_filter=action_filter,
            strategy=DeterministicActionStrategy(),
        )

        # =====================================================
        # STEP 6
        # Create the single-step executor
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
        # STEP 7
        # Capture state before autonomous continuation
        # =====================================================

        states_before = len(
            graph.states
        )

        transitions_before = (
            get_transition_count(
                graph
            )
        )

        coverage_before = (
            get_coverage_totals(
                coverage_engine
            )
        )

        print_coverage(
            "COVERAGE BEFORE COORDINATOR",
            coverage_before,
        )

        # =====================================================
        # STEP 8
        # Create coordinator
        # =====================================================

        coordinator = ExplorationCoordinator(
            target_selector=target_selector,
            step_executor=step_executor,
            limits=CoordinatorLimits(
                max_steps=coordinator_max_steps,
                max_duration=120.0,
                max_failures=3,
            ),
        )

        # =====================================================
        # STEP 9
        # Run the autonomous continuation loop
        # =====================================================

        coordinator_result = coordinator.run(
            root_state_id=root_state_id
        )

        print_coordinator_result(
            coordinator_result
        )

        print_step_history(
            coordinator_result.step_results
        )

        # =====================================================
        # STEP 10
        # Verify coordinator stop behavior
        # =====================================================

        assert (
            coordinator_result.steps
            ==
            coordinator_max_steps
        ), (
            "Coordinator did not attempt exactly the configured "
            "number of continuation steps."
        )

        assert (
            coordinator_result.stop_reason
            ==
            CoordinatorStopReason.MAX_STEPS_REACHED
        ), (
            "Coordinator did not stop at max_steps."
        )

        # =====================================================
        # STEP 11
        # Verify result accounting
        # =====================================================

        assert (
            coordinator_result.successful_steps
            +
            coordinator_result.failed_steps
            ==
            coordinator_result.steps
        ), (
            "Successful and failed step counts do not equal "
            "the total attempted steps."
        )

        assert (
            len(
                coordinator_result.step_results
            )
            ==
            coordinator_result.steps
        ), (
            "Coordinator did not preserve every step result."
        )

        # =====================================================
        # STEP 12
        # Verify each source state was a real graph state
        # =====================================================

        for step_result in (
            coordinator_result.step_results
        ):

            source_node = graph.get_state(
                step_result.source_state_id
            )

            assert source_node is not None, (
                "Coordinator attempted a source state that "
                "does not exist in StateGraph."
            )

            # TargetSelector enforces:
            #
            #     depth < max_depth
            #
            # Therefore no depth-2 state should be expanded.
            assert (
                source_node.depth
                <
                max_depth
            ), (
                "Coordinator expanded a state at or beyond "
                "the configured max_depth."
            )

        # =====================================================
        # STEP 13
        # Verify successful actions were recorded in memory
        # =====================================================

        for step_result in (
            coordinator_result.step_results
        ):

            if not step_result.execution_success:
                continue

            source_node = graph.get_state(
                step_result.source_state_id
            )

            assert (
                step_result.selected_action
                is not None
            ), (
                "Successful step contains no selected action."
            )

            assert memory.is_executed(
                source_node.state.state_hash,
                step_result.selected_action.target,
            ), (
                "Successful coordinator action was not recorded "
                "in ExplorationMemory."
            )

        # =====================================================
        # STEP 14
        # Verify transition growth
        #
        # ExplorationStepExecutor creates one transition for each
        # successfully executed action.
        # =====================================================

        transitions_after = (
            get_transition_count(
                graph
            )
        )

        assert (
            transitions_after
            ==
            transitions_before
            +
            coordinator_result.successful_steps
        ), (
            "Graph transition growth does not match successful "
            "coordinator steps."
        )

        # =====================================================
        # STEP 15
        # Verify new-state accounting
        # =====================================================

        states_after = len(
            graph.states
        )

        assert (
            states_after
            ==
            states_before
            +
            coordinator_result.new_states
        ), (
            "Graph state growth does not match coordinator "
            "new-state accounting."
        )

        # =====================================================
        # STEP 16
        # Verify result-level new-state count independently
        # =====================================================

        independently_counted_new_states = sum(
            1
            for step_result
            in coordinator_result.step_results
            if (
                step_result.execution_success
                and
                step_result.new_state_discovered
            )
        )

        assert (
            coordinator_result.new_states
            ==
            independently_counted_new_states
        ), (
            "Coordinator new-state count does not match "
            "step-result history."
        )

        # =====================================================
        # STEP 17
        # Recalculate coverage after autonomous continuation
        # =====================================================

        coverage_after = (
            get_coverage_totals(
                coverage_engine
            )
        )

        print_coverage(
            "COVERAGE AFTER COORDINATOR",
            coverage_after,
        )

        # =====================================================
        # STEP 18
        # Verify actual eligible-coverage progress
        #
        # Every successful action was previously selected from
        # unexplored eligible work.
        #
        # Therefore explored eligible actions must increase by
        # the number of successful coordinator steps.
        # =====================================================

        explored_eligible_growth = (
            coverage_after[
                "explored_eligible_actions"
            ]
            -
            coverage_before[
                "explored_eligible_actions"
            ]
        )

        assert (
            explored_eligible_growth
            ==
            coordinator_result.successful_steps
        ), (
            "Explored eligible-action coverage did not increase "
            "by the number of successful coordinator steps."
        )

        # =====================================================
        # STEP 19
        # Verify the coordinator made real progress
        # =====================================================

        assert (
            coordinator_result.successful_steps
            >
            0
        ), (
            "Coordinator completed no successful real "
            "Calculator steps."
        )

        assert (
            coverage_after[
                "explored_eligible_actions"
            ]
            >
            coverage_before[
                "explored_eligible_actions"
            ]
        ), (
            "Autonomous continuation made no eligible "
            "coverage progress."
        )

        # =====================================================
        # STEP 20
        # Print final verification
        # =====================================================

        print()
        print(
            "======================================"
        )

        print(
            "AUTONOMOUS CLOSED LOOP VERIFIED"
        )

        print(
            "======================================"
        )

        print(
            "Root State:",
            root_state_id
        )

        print(
            "Continuation Steps:",
            coordinator_result.steps
        )

        print(
            "Successful Steps:",
            coordinator_result.successful_steps
        )

        print(
            "New States:",
            coordinator_result.new_states
        )

        print(
            "Transitions Before:",
            transitions_before
        )

        print(
            "Transitions After:",
            transitions_after
        )

        print(
            "Explored Eligible Before:",
            coverage_before[
                "explored_eligible_actions"
            ]
        )

        print(
            "Explored Eligible After:",
            coverage_after[
                "explored_eligible_actions"
            ]
        )

        print()
        print(
            "CALCULATOR EXPLORATION COORDINATOR "
            "TEST PASSED"
        )


if __name__ == "__main__":

    test_calculator_exploration_coordinator()
