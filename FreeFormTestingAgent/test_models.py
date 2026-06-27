from core.models.state import ApplicationState
from core.models.action import Action, ActionType
from core.state.state_hasher import create_state_hash

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

print(state)
print()
print(action)
print()
print(state.state_hash)