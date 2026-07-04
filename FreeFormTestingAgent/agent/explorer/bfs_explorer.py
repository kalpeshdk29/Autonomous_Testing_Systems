"""
File: bfs_explorer.py

Purpose:
    Explore an application using Breadth-First Search (BFS).

    This version uses the ReplayEngine to restore the real
    application to the correct source state before executing
    every exploration action.

Architecture:

                    Root State
                        │
                        ▼
                  Exploration Queue
                        │
                        ▼
                 Select Source State
                        │
                        ▼
                Get Unexplored Actions
                        │
                        ▼
            ┌───────────────────────────┐
            │ For Every Allowed Action  │
            └─────────────┬─────────────┘
                          │
                          ▼
                Replay Root → Source
                          │
                          ▼
                 Verify Source State
                          │
                          ▼
                    Execute Action
                          │
                          ▼
                  Capture New State
                          │
                          ▼
              Store State + Transition
                          │
                          ▼
                Queue New State If New

Why Replay Is Required:
    Without replay, actions are executed sequentially against
    an already-mutated application.

    Incorrect:

        S0 --A--> S1 --B--> S2

    when the graph intended:

             --A--> S1
            /
        S0
            \
             --B--> S2

    Replay restores the real application to S0 before both
    action A and action B are executed.
"""

import time

from agent.explorer.explorer import Explorer

from agent.explorer.exploration_context import ExplorationContext

from agent.explorer.exploration_result import ExplorationResult

from agent.explorer.default_action_filter import DefaultActionFilter

from core.state.state_hasher import create_state_hash

from agent.explorer.exploration_limits import ExplorationLimits

from agent.explorer.exploration_stop_reason import ExplorationStopReason


class BFSExplorer(Explorer):
    """
    Replay-aware Breadth-First Search explorer.

    Responsibilities:
        - Capture the initial application state.
        - Maintain a BFS exploration queue.
        - Find unexplored actions.
        - Filter unsafe actions.
        - Restore source states through replay.
        - Execute actions from the correct source state.
        - Capture resulting states.
        - Store transitions.
        - Queue newly discovered states.
    """

    def __init__(
        self,
        ui,
        executor,
        graph,
        memory,
        replay_engine,
        executable: str,
        window_title: str,
        action_filter=None,
        limits=None,
    ):
        """
        Initialize the BFS explorer.

        Parameters
        ----------
        ui:
            UI adapter used to capture application states.

        executor:
            Executes Action objects against the application.

        graph:
            Stores discovered states and transitions.

        memory:
            Tracks which actions have already been executed
            from each application state.

        replay_engine:
            Restores the real application to a previously
            discovered graph state.

        executable:
            Executable used to restart the application.

            Example:
                "calc.exe"

        window_title:
            Window title used to reconnect after restart.

            Example:
                "Calculator"

        action_filter:
            Optional action filter.

            If not provided, DefaultActionFilter is used.
        """

        self.ui = ui

        self.executor = executor

        self.graph = graph

        self.memory = memory

        self.replay_engine = replay_engine

        self.executable = executable

        self.window_title = window_title

        self.action_filter = action_filter or DefaultActionFilter()

        #
        # Use caller-provided limits when available.
        #
        # Otherwise, use safe default exploration limits.
        #
        self.limits = limits or ExplorationLimits()

    def explore(self, window) -> ExplorationResult:
        """
        Explore the application using replay-aware BFS.

        Parameters
        ----------
        window:
            Initial connected application window.

        max_states:
            Maximum number of unique states to discover.

        Returns
        -------
        ExplorationResult:
            Statistics for the completed exploration session.
        """

        start_time = time.time()

        context = ExplorationContext()

        # =====================================================
        # STEP 1
        # Capture and store the root state
        # =====================================================

        root_state = self.ui.capture_state(window)

        root_state.state_hash = create_state_hash(root_state)

        # =====================================================
        # The initial application state is always the root
        # of the current exploration session.
        #
        # Therefore, its BFS depth is zero.
        # =====================================================

        root_id = self.graph.add_state(root_state, depth=0)

        context.enqueue(root_id)

        context.total_states = 1

        print()
        print("===== BFS EXPLORATION STARTED =====")

        print("Root State:", root_id)

        # =====================================================
        # STEP 2
        # Process states in BFS order
        # =====================================================

        while context.has_states():

            if self._should_stop(context, start_time):
                break

            source_id = context.dequeue()

            # Avoid fully processing the same state twice.
            if source_id in context.visited_states:
                continue

            source_node = self.graph.get_state(source_id)

            if source_node is None:

                print(f"State not found in graph: " f"{source_id}")

                continue

            source_state = source_node.state

            # =====================================================
            # Read the shortest known depth of the source state.
            # =====================================================

            source_depth = self.graph.get_state_depth(source_id)

            if source_depth is None:

                print("Unable to determine state depth:", source_id)

                continue

            print()
            print("======================================")

            print("Exploring State:", source_id)

            print("State Depth:", source_depth)

            print("State Hash:", source_state.state_hash)

            # =====================================================
            # DEPTH BOUNDARY
            #
            # States at max_depth are valid discovered states.
            # They remain stored in the graph.
            #
            # However, their outgoing actions must not be explored.
            #
            # Example:
            #
            #     max_depth = 2
            #
            #     S0 [0]  → explore
            #     S1 [1]  → explore
            #     S2 [2]  → store only
            # =====================================================

            if (
                self.limits.max_depth is not None
                and source_depth >= self.limits.max_depth
            ):

                print("Maximum depth reached for state.")

                print("Skipping expansion:", source_id)

                context.visited_states.add(source_id)

                continue

            # =================================================
            # STEP 3
            # Find unexplored actions for this state
            # =================================================

            unexplored_actions = self.memory.get_unexplored_actions(
                source_state.state_hash, source_state.available_actions
            )

            # =================================================
            # STEP 4
            # Remove unsafe or unwanted actions
            # =================================================

            allowed_actions = [
                action
                for action in unexplored_actions
                if self.action_filter.allow(action)
            ]

            print("Unexplored Actions:", len(unexplored_actions))

            print("Allowed Actions:", len(allowed_actions))

            # =================================================
            # STEP 5
            # Explore every allowed action
            # =================================================

            for action in allowed_actions:

                # Stop immediately when the unique-state limit
                # has been reached.
                if self._should_stop(context, start_time):
                    break

                print()
                print("--------------------------------------")

                print("Source:", source_id)

                print("Action:", action.target)

                # =============================================
                # STEP 5.1
                # Restore the real application to the source
                # state before executing this action.
                # =============================================

                replayed_window = self.replay_engine.replay(
                    executable=self.executable,
                    window_title=self.window_title,
                    source_state=root_id,
                    target_state=source_id,
                )

                if replayed_window is None:

                    print("Unable to restore source state.")

                    print("Skipping action:", action.target)

                    continue

                # =============================================
                # STEP 5.2
                # Execute the action from the verified source
                # state.
                # =============================================

                action_start_time = time.time()

                success = self.executor.execute(replayed_window, action)

                action_duration = time.time() - action_start_time

                # The action has now been attempted from this
                # source state, so record it in exploration
                # memory.
                self.memory.mark_executed(source_state.state_hash, action.target)

                context.total_actions += 1

                if not success:

                    context.total_failures += 1

                    print("Action execution failed:", action.target)

                    continue

                # =============================================
                # STEP 5.3
                # Capture the application after the action.
                # =============================================

                target_state = self.ui.capture_state(replayed_window)

                target_state.state_hash = create_state_hash(target_state)

                # =====================================================
                # Check whether this state is genuinely new before
                # adding it to the graph.
                # =====================================================

                # =====================================================
                # Check whether the observed target is genuinely new.
                # =====================================================

                is_new_state = not self.graph.has_state(
                    target_state.state_hash
                )

                # =====================================================
                # Enforce the state admission limit BEFORE adding a
                # genuinely new state to the graph.
                # =====================================================

                if (
                    is_new_state
                    and
                    not self._can_add_new_state(context)
                ):
                    print(
                        "State limit reached."
                    )

                    print(
                        "Skipping new target state:",
                        target_state.state_hash
                    )

                    continue

                # =====================================================
                # Calculate the candidate BFS depth.
                # =====================================================

                target_depth = source_depth + 1

                # =====================================================
                # Add the state exactly ONCE.
                #
                # For a new state:
                #     stores target_depth.
                #
                # For an existing state:
                #     StateGraph should preserve the shortest depth.
                # =====================================================

                target_id = self.graph.add_state(
                    target_state,
                    depth=target_depth
                )

                stored_target_depth = (
                    self.graph.get_state_depth(
                        target_id
                    )
                )

                # =====================================================
                # Store the transition.
                # =====================================================

                self.graph.add_transition(
                    source_id,
                    action,
                    target_id,
                    success=success,
                    duration=action_duration,
                )

                context.total_transitions += 1

                print(
                    "Target:",
                    target_id
                )

                print(
                    "Target Depth:",
                    stored_target_depth
                )

                print(
                    "New State:",
                    is_new_state
                )

                # =====================================================
                # Queue only genuinely new states.
                # =====================================================

                if is_new_state:

                    context.enqueue(
                        target_id
                    )

                    context.total_states += 1

                    print(
                        "Queued New State:",
                        target_id
                    )

            context.visited_states.add(source_id)

        # =====================================================
        # Determine final stop reason
        # =====================================================

        if context.stop_reason is None:

            context.stop_reason = ExplorationStopReason.COMPLETED

        # =====================================================
        # STEP 6
        # Finish exploration
        # =====================================================

        duration = time.time() - start_time

        print()
        print("===== BFS EXPLORATION FINISHED =====")

        print("States:", context.total_states)

        print("Transitions:", context.total_transitions)

        print("Actions:", context.total_actions)

        print("Duration:", duration)

        print("Failures:", context.total_failures)

        print("Stop Reason:", context.stop_reason.value)

        return ExplorationResult(
            states=context.total_states,
            transitions=context.total_transitions,
            actions=context.total_actions,
            failures=context.total_failures,
            duration=duration,
            stop_reason=context.stop_reason,
        )

    def _should_stop(self, context, start_time) -> bool:
        """
        Check all configured exploration limits.

        If a limit has been reached, store the
        stop reason in the exploration context.

        Returns
        -------
        bool:
            True when exploration must stop.
        """

        stop_reason = self._get_stop_reason(context, start_time)

        if stop_reason is None:
            return False

        context.stop_reason = stop_reason

        print()
        print("===== EXPLORATION LIMIT REACHED =====")

        print("Stop Reason:", stop_reason.value)

        return True

    def _can_add_new_state(self, context) -> bool:
        """
        Check whether another unique state may be added.

        Reaching the state limit does not terminate BFS.

        Already-discovered and queued states may still
        be explored.
        """

        if self.limits.max_states is None:
            return True

        return context.total_states < self.limits.max_states

    def _get_stop_reason(self, context, start_time):
        """
        Check whether any exploration limit
        has been reached.

        Parameters
        ----------
        context:
            Current ExplorationContext.

        start_time:
            Timestamp when exploration started.

        Returns
        -------
        ExplorationStopReason | None:
            Stop reason when a limit is reached.

            None when exploration may continue.
        """

        elapsed_time = time.time() - start_time

        # =====================================================
        # Action Limit
        # =====================================================

        if (
            self.limits.max_actions is not None
            and context.total_actions >= self.limits.max_actions
        ):
            return ExplorationStopReason.MAX_ACTIONS_REACHED

        # =====================================================
        # Transition Limit
        # =====================================================

        if (
            self.limits.max_transitions is not None
            and context.total_transitions >= self.limits.max_transitions
        ):
            return ExplorationStopReason.MAX_TRANSITIONS_REACHED

        # =====================================================
        # Duration Limit
        # =====================================================

        if (
            self.limits.max_duration is not None
            and elapsed_time >= self.limits.max_duration
        ):
            return ExplorationStopReason.MAX_DURATION_REACHED

        # =====================================================
        # Failure Limit
        # =====================================================

        if (
            self.limits.max_failures is not None
            and context.total_failures >= self.limits.max_failures
        ):
            return ExplorationStopReason.MAX_FAILURES_REACHED

        return None
