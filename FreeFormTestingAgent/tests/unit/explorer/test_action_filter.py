"""
Test action filtering.
"""

from agent.explorer.default_action_filter import (
    DefaultActionFilter
)

from core.models.action import (
    Action,
    ActionType
)


def test_action_filter():

    filter = (
        DefaultActionFilter()
    )

    action1 = Action(
        action_type=ActionType.CLICK,
        target="Minimize"
    )

    action2 = Action(
        action_type=ActionType.CLICK,
        target="num7Button"
    )

    assert (
        filter.allow(
            action1
        )
        is False
    )

    assert (
        filter.allow(
            action2
        )
        is True
    )

    print()
    print(
        "TEST PASSED"
    )


if __name__ == "__main__":
    test_action_filter()