from core.models.state import ApplicationState
from core.models.action import Action, ActionType
from core.state.state_hasher import create_state_hash
from agent.explorer.action_discovery import ActionDiscovery

state = ApplicationState(
    window_title="Calculator",
    controls=[
        {"id":"btn_7","name":"7"},
        {"id":"btn_plus","name":"+"}
    ],
    values={
        "display":"7"
    }
)

state.state_hash = create_state_hash(state)

action = Action(
    action_type=ActionType.CLICK,
    target="btn_7"
)

discover = ActionDiscovery()

actions = discover.discover(
    state.controls
)

print()

for a in actions:
    print(a)

