"""
File: replay_engine.py

Purpose:
    Restore previously discovered
    application states by replaying
    transitions.

Architecture:

Target State
        ↓
StateGraph
        ↓
Transition Path
        ↓
Restart Application
        ↓
Replay Actions
        ↓
Target State
"""

import time
from core.state.state_hasher import create_state_hash

class ReplayEngine:
    """
    Replays application states.
    """

    def __init__(
        self,
        ui,
        executor,
        graph
    ):
        """
        Initialize replay engine.
        """

        self.ui = ui

        self.executor = executor

        self.graph = graph

    def replay(
        self,
        executable: str,
        window_title: str,
        source_state: str,
        target_state: str
    ):
        """
        Replay path from source state
        to target state.

        Parameters
        ----------
        executable:
            Application executable.

        window_title:
            Window title.

        source_state:
            Starting state.

        target_state:
            Destination state.

        Returns
        -------
        Window object or None.
        """

        #
        # Find transition path
        #
        transitions = (
            self.graph.find_transition_path(
                source_state,
                target_state
            )
        )

        if transitions is None:

            print(
                "Replay path not found."
            )

            return None

        #
        # Restart application
        #
        print()
        print(
            "===== RESTART ====="
        )

        self.ui.kill_application()

        self.ui.launch_application(
            executable
        )

        time.sleep(1)

        window = (
            self.ui.connect_window(
                window_title
            )
        )

        #
        # Replay transitions
        #
        print()
        print(
            "===== REPLAY ====="
        )

        for transition in transitions:

            action = transition.action

            print(
                f"Replay:"
                f" {action.target}"
            )

            success = (
                self.executor.execute(
                    window,
                    action
                )
            )

            if not success:

                print(
                   "Replay action execution failed."
                )

                return None

        print()
        print(
            "Replay complete."
        )

        # =====================================================
        # Replay Verification
        # =====================================================

        print()
        print("===== VERIFY REPLAY =====")

        # Retrieve the target state that was originally
        # discovered and stored inside the graph.
        target_node = self.graph.get_state(
            target_state
        )

        if target_node is None:

            print(
                f"Target state not found in graph: "
                f"{target_state}"
            )

            return None

        expected_state = target_node.state

        # Capture the real application state after all
        # replay actions have been executed.
        actual_state = self.ui.capture_state(
            window
        )

        # Generate the same deterministic hash used
        # during the original exploration.
        actual_state.state_hash = create_state_hash(
            actual_state
        )

        print(
            "Expected:",
            expected_state.state_hash
        )

        print(
            "Actual:  ",
            actual_state.state_hash
        )

        # The replay is successful only when the real
        # application reaches the expected target state.
        if (
            actual_state.state_hash
            != expected_state.state_hash
        ):

            print()
            print(
                "Replay verification failed."
            )

            return None

        print()
        print(
            "Replay verified successfully."
        )

        return window
