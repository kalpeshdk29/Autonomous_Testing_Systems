"""
Unit tests for ExplorationStepExecutor.

These tests isolate one exploration step from the real UI.

Controlled success flow:

    S0
        ↓ replay
    S1
        ↓ select CLICK(buttonB)
        ↓ execute
    S2

What These Tests Prove:

    1. Missing source state is handled.
    2. No remaining action is handled.
    3. Replay failure stops execution.
    4. Failed execution is recorded in memory.
    5. Successful execution captures and stores a state.
    6. A transition is created.
    7. Existing target states are deduplicated.
"""

from core.models.action import Action

from core.models.action_type import (
    ActionType,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.explorer.exploration_step_executor import (
    ExplorationStepExecutor,
)


class FakeApplicationState:
    """
    Minimal state object needed by the step executor.
    """

    def __init__(
        self,
        state_id,
        state_hash,
        available_actions,
    ):
        self.state_id = state_id

        self.state_hash = state_hash

        self.available_actions = available_actions

        # Required by the real state hasher.
        self.window_title = "Test"

        self.controls = []

        self.values = {}


class FakeStateNode:
    """
    Minimal replacement for StateNode.
    """

    def __init__(
        self,
        state,
        depth,
    ):
        self.state = state

        self.depth = depth


class FakeGraph:
    """
    Controlled graph implementation for isolated tests.
    """

    def __init__(self):
        self.states = {}

        self.hash_index = {}

        self.transitions = []

    def add_existing_state(
        self,
        state,
        depth,
    ):
        self.states[state.state_id] = (
            FakeStateNode(
                state,
                depth,
            )
        )

        self.hash_index[
            state.state_hash
        ] = state.state_id

    def get_state(
        self,
        state_id,
    ):
        return self.states.get(
            state_id
        )

    def get_state_depth(
        self,
        state_id,
    ):
        node = self.get_state(
            state_id
        )

        if node is None:
            return None

        return node.depth

    def has_state(
        self,
        state_hash,
    ):
        return (
            state_hash
            in
            self.hash_index
        )

    def add_state(
        self,
        state,
        depth=0,
    ):
        if state.state_hash in self.hash_index:

            return self.hash_index[
                state.state_hash
            ]

        self.add_existing_state(
            state,
            depth,
        )

        return state.state_id

    def add_transition(
        self,
        source_id,
        action,
        target_id,
        success=True,
        duration=0.0,
    ):
        transition = {
            "source_state": source_id,
            "action": action,
            "target_state": target_id,
            "success": success,
            "duration": duration,
        }

        self.transitions.append(
            transition
        )

        return transition


class FakeUI:
    """
    Return a predefined resulting state.
    """

    def __init__(
        self,
        target_state,
    ):
        self.target_state = target_state

    def capture_state(
        self,
        window,
    ):
        return self.target_state


class FakeExecutor:
    """
    Controlled action execution result.
    """

    def __init__(
        self,
        success=True,
    ):
        self.success = success

        self.executed_actions = []

    def execute(
        self,
        window,
        action,
    ):
        self.executed_actions.append(
            action
        )

        return self.success


class FakeReplayEngine:
    """
    Controlled replay result.
    """

    def __init__(
        self,
        window="fake_window",
    ):
        self.window = window

    def replay(
        self,
        executable,
        window_title,
        source_state,
        target_state,
    ):
        return self.window


class FakeActionSelector:
    """
    Controlled action selection result.
    """

    def __init__(
        self,
        action,
    ):
        self.action = action

    def select_next_action(
        self,
        state_hash,
        actions,
    ):
        return self.action


def create_fixture(
    replay_window="fake_window",
    execution_success=True,
    selected_action=True,
):
    """
    Build the common controlled test fixture.
    """

    action = Action(
        action_type=ActionType.CLICK,
        target="buttonB",
    )

    source_state = FakeApplicationState(
        state_id="S1",
        state_hash="source_hash",
        available_actions=[action],
    )

    target_state = FakeApplicationState(
        state_id="S2",
        state_hash="",
        available_actions=[],
    )

    graph = FakeGraph()

    graph.add_existing_state(
        source_state,
        depth=1,
    )

    memory = ExplorationMemory()

    executor = FakeExecutor(
        success=execution_success,
    )

    replay_engine = FakeReplayEngine(
        window=replay_window,
    )

    action_selector = FakeActionSelector(
        action=(
            action
            if selected_action
            else None
        )
    )

    ui = FakeUI(
        target_state=target_state,
    )

    step_executor = ExplorationStepExecutor(
        ui=ui,
        executor=executor,
        graph=graph,
        memory=memory,
        replay_engine=replay_engine,
        action_selector=action_selector,
        executable="test.exe",
        window_title="Test",
    )

    return (
        step_executor,
        graph,
        memory,
        executor,
        source_state,
        target_state,
        action,
    )


def test_missing_source_state_is_handled():
    """
    Unknown source IDs must fail before replay or execution.
    """

    (
        step_executor,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_fixture()

    result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="UNKNOWN",
    )

    assert result.execution_success is False

    assert (
        result.failure_reason
        ==
        "SOURCE_STATE_NOT_FOUND"
    )


def test_no_eligible_action_is_handled():
    """
    A state with no selectable action must return a clean result.
    """

    (
        step_executor,
        _,
        _,
        _,
        _,
        _,
        _,
    ) = create_fixture(
        selected_action=False
    )

    result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="S1",
    )

    assert result.selected_action is None

    assert (
        result.failure_reason
        ==
        "NO_ELIGIBLE_ACTION"
    )


def test_replay_failure_stops_execution():
    """
    Action execution must not occur when replay fails.
    """

    (
        step_executor,
        _,
        _,
        executor,
        _,
        _,
        _,
    ) = create_fixture(
        replay_window=None
    )

    result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="S1",
    )

    assert result.replay_success is False

    assert len(
        executor.executed_actions
    ) == 0

    assert (
        result.failure_reason
        ==
        "REPLAY_FAILED"
    )


def test_failed_execution_is_recorded_in_memory():
    """
    Attempted actions must be remembered even when execution fails.
    """

    (
        step_executor,
        _,
        memory,
        _,
        source_state,
        _,
        action,
    ) = create_fixture(
        execution_success=False
    )

    result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="S1",
    )

    assert result.replay_success is True

    assert result.execution_success is False

    assert memory.is_executed(
        source_state.state_hash,
        action.target,
    )

    assert (
        result.failure_reason
        ==
        "ACTION_EXECUTION_FAILED"
    )


def test_successful_step_updates_graph_and_memory():
    """
    A successful step must store the target and transition.
    """

    (
        step_executor,
        graph,
        memory,
        _,
        source_state,
        _,
        action,
    ) = create_fixture()

    result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="S1",
    )

    assert result.replay_success is True

    assert result.execution_success is True

    assert result.target_state_id == "S2"

    assert result.transition is not None

    assert result.new_state_discovered is True

    assert len(
        graph.transitions
    ) == 1

    assert memory.is_executed(
        source_state.state_hash,
        action.target,
    )


def test_existing_target_state_is_deduplicated():
    """
    Reaching an existing hash must not be reported as a new state.
    """

    (
        step_executor,
        graph,
        _,
        _,
        _,
        target_state,
        _,
    ) = create_fixture()

    # The real hasher will replace target_state.state_hash.
    #
    # Capture the hash by executing one first controlled step.
    first_result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="S1",
    )

    assert first_result.new_state_discovered is True

    # Execute again against the same captured target state.
    second_result = step_executor.execute_step(
        root_state_id="S0",
        source_state_id="S1",
    )

    assert second_result.new_state_discovered is False

    assert (
        second_result.target_state_id
        ==
        first_result.target_state_id
    )


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_missing_source_state_is_handled,
        test_no_eligible_action_is_handled,
        test_replay_failure_stops_execution,
        test_failed_execution_is_recorded_in_memory,
        test_successful_step_updates_graph_and_memory,
        test_existing_target_state_is_deduplicated,
    ]

    print()
    print(
        "===== EXPLORATION STEP EXECUTOR TESTS ====="
    )
    print()

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()
    print(
        "All ExplorationStepExecutor tests passed successfully."
    )


if __name__ == "__main__":

    main()