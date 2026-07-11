"""
File: failure_record.py

Purpose:
    Store one structured deterministic failure discovered during
    autonomous exploration.

Architecture:

Failure Observation
        ↓
Failure Classification
        ↓
FailureRecord
        ↓
Persistence / Reporting / Reproduction

Why This Component Exists:
    Console messages are not sufficient for an autonomous testing
    framework.

    A discovered failure must preserve enough structured context
    to support:

        - persistence
        - reporting
        - evidence collection
        - deduplication
        - reproduction
        - future AI interpretation

Important:
    FailureRecord stores facts about a discovered failure.

    It does not decide:

        - whether exploration should stop
        - whether recovery should be attempted
        - whether the failure is important

    Those decisions belong to higher-level policy components.
"""

from dataclasses import dataclass, field

from datetime import datetime

from typing import Any

from uuid import uuid4


from core.models.action import (
    Action,
)

from core.models.transition import (
    Transition,
)

from agent.failure.failure_type import (
    FailureType,
)


@dataclass
class FailureRecord:
    """
    Structured record of one deterministic exploration failure.

    Attributes
    ----------
    failure_type:
        Stable classification of what failed.

    message:
        Human-readable explanation of the failure.

    source_state_id:
        Graph state from which the failing operation began.

    action:
        Action associated with the failure, when available.

    target_state_id:
        Resulting or expected target state, when available.

    replay_path:
        Ordered transitions used to reach the source state.

        This creates the foundation for future automatic failure
        reproduction.

    screenshot_path:
        Durable screenshot evidence location, when available.

    recoverable:
        Whether exploration may safely continue after the failure.

        This is stored as an observed or policy-provided fact.

        The FailureRecord itself does not perform recovery.

    metadata:
        Additional structured information specific to a detector.

    failure_id:
        Unique identity of this failure occurrence.

    timestamp:
        Time when the failure record was created.
    """

    failure_type: FailureType

    message: str

    source_state_id: str

    action: Action | None = None

    target_state_id: str | None = None

    replay_path: list[Transition] = field(
        default_factory=list
    )

    screenshot_path: str | None = None

    recoverable: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    failure_id: str = field(
        default_factory=lambda: str(
            uuid4()
        )
    )

    timestamp: datetime = field(
        default_factory=datetime.now
    )

    def __post_init__(
        self,
    ):
        """
        Validate the minimum stable failure contract.
        """

        if not isinstance(
            self.failure_type,
            FailureType,
        ):

            raise ValueError(
                "failure_type must be a "
                "FailureType."
            )

        if not isinstance(
            self.message,
            str,
        ):

            raise ValueError(
                "message must be a string."
            )

        if not self.message.strip():

            raise ValueError(
                "message cannot be empty."
            )

        if not isinstance(
            self.source_state_id,
            str,
        ):

            raise ValueError(
                "source_state_id must be "
                "a string."
            )

        if not self.source_state_id.strip():

            raise ValueError(
                "source_state_id cannot "
                "be empty."
            )

        if (
            self.action is not None
            and
            not isinstance(
                self.action,
                Action,
            )
        ):

            raise ValueError(
                "action must be an Action "
                "or None."
            )

        if not isinstance(
            self.replay_path,
            list,
        ):

            raise ValueError(
                "replay_path must be a list."
            )

        for transition in self.replay_path:

            if not isinstance(
                transition,
                Transition,
            ):

                raise ValueError(
                    "replay_path must contain "
                    "only Transition objects."
                )

        if not isinstance(
            self.recoverable,
            bool,
        ):

            raise ValueError(
                "recoverable must be a bool."
            )

        if not isinstance(
            self.metadata,
            dict,
        ):

            raise ValueError(
                "metadata must be a dictionary."
            )