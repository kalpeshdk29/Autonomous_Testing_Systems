"""
Execute exactly one controlled exploration step.

Architecture:

Selected Exploration Target
        ↓
Resolve Source State
        ↓
Select One Action
        ↓
Replay Root → Source
        ↓
Execute Action
        ↓
Capture Resulting State
        ↓
Update Graph + Memory
        ↓
ExplorationStepResult
"""

import time

from core.state.state_hasher import (
    create_state_hash,
)

from agent.explorer.exploration_step_result import (
    ExplorationStepResult,
)


class ExplorationStepExecutor:
    """
    Execute one exploration decision.

    This component deliberately performs only one step.

    It does not:
        - calculate coverage
        - select the exploration target
        - repeat exploration
        - enforce session-wide limits

    Those responsibilities belong to the future
    ExplorationCoordinator.
    """

    def __init__(
        self,
        ui,
        executor,
        graph,
        memory,
        replay_engine,
        action_selector,
        executable: str,
        window_title: str,
    ) -> None:
        """
        Initialize the single-step executor.

        Args:
            ui:
                UI adapter used to capture application states.

            executor:
                Existing ActionExecutor.

            graph:
                Existing StateGraph.

            memory:
                Existing ExplorationMemory.

            replay_engine:
                Existing ReplayEngine.

            action_selector:
                Existing ActionSelector.

            executable:
                Application executable used by replay.

            window_title:
                Application window title used by replay.
        """

        self.ui = ui

        self.executor = executor

        self.graph = graph

        self.memory = memory

        self.replay_engine = replay_engine

        self.action_selector = action_selector

        self.executable = executable

        self.window_title = window_title

    def execute_step(
        self,
        root_state_id: str,
        source_state_id: str,
    ) -> ExplorationStepResult:
        """
        Execute exactly one unexplored eligible action from
        the requested source state.

        Args:
            root_state_id:
                Graph ID of the exploration root.

                ReplayEngine requires this because it restores:

                    root → source

            source_state_id:
                Graph ID of the state to continue exploring.

        Returns:
            ExplorationStepResult describing the complete outcome.
        """

        # =====================================================
        # STEP 1
        # Resolve source state
        # =====================================================

        source_node = self.graph.get_state(
            source_state_id
        )

        if source_node is None:

            return ExplorationStepResult(
                source_state_id=source_state_id,
                failure_reason="SOURCE_STATE_NOT_FOUND",
            )

        source_state = source_node.state

        # =====================================================
        # STEP 2
        # Select one remaining eligible action
        # =====================================================

        selected_action = (
            self.action_selector.select_next_action(
                state_hash=source_state.state_hash,
                actions=source_state.available_actions,
            )
        )

        if selected_action is None:

            return ExplorationStepResult(
                source_state_id=source_state_id,
                failure_reason="NO_ELIGIBLE_ACTION",
            )

        # =====================================================
        # STEP 3
        # Restore and verify the real source state
        # =====================================================

        replayed_window = self.replay_engine.replay(
            executable=self.executable,
            window_title=self.window_title,
            source_state=root_state_id,
            target_state=source_state_id,
        )

        if replayed_window is None:

            return ExplorationStepResult(
                source_state_id=source_state_id,
                selected_action=selected_action,
                failure_reason="REPLAY_FAILED",
            )

        # =====================================================
        # STEP 4
        # Execute exactly one action
        # =====================================================

        action_start_time = time.time()

        execution_success = self.executor.execute(
            replayed_window,
            selected_action,
        )

        action_duration = (
            time.time() - action_start_time
        )

        # Preserve existing BFS semantics:
        #
        # An attempted action is recorded even when execution
        # fails. Otherwise the same failing action could be
        # selected indefinitely.
        self.memory.mark_executed(
            source_state.state_hash,
            selected_action.target,
        )

        if not execution_success:

            return ExplorationStepResult(
                source_state_id=source_state_id,
                selected_action=selected_action,
                replay_success=True,
                execution_success=False,
                duration=action_duration,
                failure_reason="ACTION_EXECUTION_FAILED",
            )

        # =====================================================
        # STEP 5
        # Capture and hash resulting application state
        # =====================================================

        target_state = self.ui.capture_state(
            replayed_window
        )

        target_state.state_hash = create_state_hash(
            target_state
        )

        # =====================================================
        # STEP 6
        # Determine whether result is genuinely new
        # =====================================================

        is_new_state = not self.graph.has_state(
            target_state.state_hash
        )

        # =====================================================
        # STEP 7
        # Calculate candidate graph depth
        # =====================================================

        source_depth = self.graph.get_state_depth(
            source_state_id
        )

        if source_depth is None:

            return ExplorationStepResult(
                source_state_id=source_state_id,
                selected_action=selected_action,
                replay_success=True,
                execution_success=True,
                duration=action_duration,
                failure_reason="SOURCE_DEPTH_NOT_FOUND",
            )

        target_depth = source_depth + 1

        # =====================================================
        # STEP 8
        # Add or deduplicate target state
        # =====================================================

        target_state_id = self.graph.add_state(
            target_state,
            depth=target_depth,
        )

        # =====================================================
        # STEP 9
        # Store transition
        # =====================================================

        transition = self.graph.add_transition(
            source_state_id,
            selected_action,
            target_state_id,
            success=True,
            duration=action_duration,
        )

        # =====================================================
        # STEP 10
        # Return structured success result
        # =====================================================

        return ExplorationStepResult(
            source_state_id=source_state_id,
            selected_action=selected_action,
            target_state_id=target_state_id,
            transition=transition,
            replay_success=True,
            execution_success=True,
            new_state_discovered=is_new_state,
            duration=action_duration,
            failure_reason=None,
        )