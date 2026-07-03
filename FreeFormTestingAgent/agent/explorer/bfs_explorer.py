"""
File: bfs_explorer.py

Purpose:
    Breadth First Search explorer.

Architecture:

Queue
    ↓
State
    ↓
Action
    ↓
Execute
    ↓
Capture
    ↓
Graph
"""

import time

from agent.explorer.explorer import Explorer
from agent.explorer.exploration_context import (
    ExplorationContext
)
from agent.explorer.exploration_result import (
    ExplorationResult
)

from core.state.state_hasher import (
    create_state_hash
)

from agent.explorer.default_action_filter import (
    DefaultActionFilter
)


class BFSExplorer(Explorer):
    """
    Breadth First Explorer.
    """

    def __init__(
    self,
    ui,
    executor,
    graph,
    memory,
    action_filter=None
    ):

        self.ui = ui

        self.executor = executor

        self.graph = graph

        self.memory = memory

        self.action_filter = (
            action_filter
            or
            DefaultActionFilter()
        )

    def explore(
        self,
        window,
        max_states: int = 10
    ) -> ExplorationResult:
        """
        Explore application.
        """

        start = time.time()

        context = (
            ExplorationContext()
        )

        #
        # Capture initial state
        #
        initial_state = (
            self.ui.capture_state(
                window
            )
        )

        initial_state.state_hash = (
            create_state_hash(
                initial_state
            )
        )

        root_id = (
            self.graph.add_state(
                initial_state
            )
        )

        context.enqueue(
            root_id
        )

        context.total_states = 1

        #
        # BFS
        #
        while (
            context.has_states()
            and
            context.total_states
            < max_states
        ):

            state_id = (
                context.dequeue()
            )

            node = (
                self.graph.get_state(
                    state_id
                )
            )

            current_state = (
                node.state
            )

            print()
            print(
                f"Exploring:"
                f" {state_id}"
            )

            actions = (
                self.memory
                .get_unexplored_actions(
                    current_state.state_hash,
                    current_state.available_actions
                )
            )

            for action in current_state.available_actions:

                allowed = (
                    self.action_filter.allow(
                        action
                    )
                )

                print(
                    f"{action.target}"
                    f" -> "
                    f"{'ALLOW' if allowed else 'BLOCK'}"
                )

            actions = [

                action

                for action in actions

                if self.action_filter.allow(
                    action
                )
            ]

            for action in actions:

                print(
                    f"Executing:"
                    f" {action.target}"
                )

                success = (
                    self.executor.execute(
                        window,
                        action
                    )
                )

                self.memory.mark_executed(
                    current_state.state_hash,
                    action.target
                )

                next_state = (
                    self.ui.capture_state(
                        window
                    )
                )

                next_state.state_hash = (
                    create_state_hash(
                        next_state
                    )
                )

                next_id = (
                    self.graph.add_state(
                        next_state
                    )
                )

                self.graph.add_transition(
                    state_id,
                    action,
                    next_id,
                    success
                )

                context.total_actions += 1

                context.total_transitions += 1

                if next_id != state_id:

                    context.enqueue(
                        next_id
                    )

                    context.total_states += 1

                if (
                    context.total_states
                    >= max_states
                ):
                    break

        duration = (
            time.time()
            - start
        )

        return ExplorationResult(
            states=context.total_states,
            transitions=context.total_transitions,
            actions=context.total_actions,
            duration=duration
        )