import json
import hashlib

from core.models.state import ApplicationState


def create_state_hash(
        state: ApplicationState
) -> str:

    data = {
        "window": state.window_title,
        "controls": state.controls,
        "values": state.values,
    }

    serialized = json.dumps(
        data,
        sort_keys=True
    )

    return hashlib.sha256(
        serialized.encode()
    ).hexdigest()