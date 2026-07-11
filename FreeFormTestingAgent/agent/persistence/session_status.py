"""
File: session_status.py

Purpose:
    Define the durable lifecycle state of an exploration session.

Architecture:

Session Created
    ↓
CREATED
    ↓
RUNNING
    ↓
    ├── COMPLETED
    └── FAILED

Unexpected Process Termination:

RUNNING persisted on disk
    ↓
Process disappears before final status update
    ↓
Next runtime loads RUNNING
    ↓
Previous execution is treated as interrupted
    ↓
Resume from latest durable checkpoint

Important:
    INTERRUPTED is intentionally not stored as a primary runtime
    status.

    A process that crashes cannot reliably update its own status.

    Therefore, a persisted RUNNING session discovered by a new
    runtime represents an interrupted previous execution.
"""

from enum import Enum


class SessionStatus(Enum):
    """
    Durable lifecycle status of an exploration session.

    CREATED:
        Session exists but autonomous exploration has not started.

    RUNNING:
        Exploration is active.

        If a future runtime loads a session still marked RUNNING,
        the previous execution did not complete cleanly.

    COMPLETED:
        Exploration ended successfully.

    FAILED:
        Exploration ended because of an unrecoverable failure.
    """

    CREATED = "CREATED"

    RUNNING = "RUNNING"

    COMPLETED = "COMPLETED"

    FAILED = "FAILED"