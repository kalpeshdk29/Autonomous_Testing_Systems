"""
File: state_hasher.py

Purpose:
    Create a deterministic hash for an ApplicationState.

Why:
    Two states that have the same UI structure and
    values should produce the same hash.

Architecture:

ApplicationState
        ↓
Serializable Dict
        ↓
JSON
        ↓
SHA256
"""

import json
import hashlib

from core.models.state import ApplicationState


def create_state_hash(
        state: ApplicationState
) -> str:
    """
    Create a deterministic hash for an application state.

    Args:
        state:
            ApplicationState object.

    Returns:
        SHA256 hash string.
    """

    # Convert Pydantic UIControl objects into
    # JSON serializable dictionaries
    serialized_controls = []

    for control in state.controls:

        serialized_controls.append(
            control.model_dump()
        )

    data = {

        # Window title
        "window":
            state.window_title,

        # UI structure
        "controls":
            serialized_controls,

        # Dynamic values
        "values":
            state.values,
    }

    serialized = json.dumps(
        data,
        sort_keys=True
    )

    return hashlib.sha256(
        serialized.encode()
    ).hexdigest()