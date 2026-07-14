"""
File: recovery_context.py

Purpose:
    Hold the runtime dependencies required by recovery policies.

Architecture:

ExplorationCoordinator
        │
        ▼
RecoveryManager
        │
        ▼
RecoveryContext
        │
        ▼
RecoveryPolicy

Important:

    RecoveryContext is NOT persisted.

    It contains live runtime objects required to perform recovery,
    such as replay engines and UI adapters.

    Historical evidence belongs in FailureRecord.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryContext:
    """
    Runtime information required to perform recovery.
    """

    executable: str

    window_title: str

    ui_adapter: object

    replay_engine: object

    graph: object

    memory: object

    root_state_id: str

    def __post_init__(self):

        if (
            not isinstance(
                self.executable,
                str,
            )
            or
            not self.executable.strip()
        ):

            raise ValueError(
                "executable must be a non-empty string."
            )

        if (
            not isinstance(
                self.window_title,
                str,
            )
            or
            not self.window_title.strip()
        ):

            raise ValueError(
                "window_title must be a non-empty string."
            )
        
        if (
            not isinstance(
                self.root_state_id,
                str,
            )
            or
            not self.root_state_id.strip()
        ):

            raise ValueError(
                "root_state_id must be a non-empty string."
            )

        for name in (
            "ui_adapter",
            "replay_engine",
            "graph",
            "memory",
        ):

            if getattr(self, name) is None:

                raise ValueError(
                    f"{name} is required."
                )