"""
Unit tests for ActionSelector.

Controlled scenario:

    State Hash:
        state_hash_1

    Available Actions:
        CLICK(num8Button)
        CLICK(num7Button)
        CLICK(closeButton)
        CLICK(plusButton)

    ExplorationMemory:
        num7Button already executed

    ActionFilter:
        closeButton blocked

Expected candidates:
        num8Button
        plusButton

Expected deterministic ranking:
        num8Button
        plusButton

Expected selected action:
        num8Button

What These Tests Prove:

    1. Already executed actions are excluded.
    2. Blocked actions are excluded.
    3. Valid candidates are preserved.
    4. Candidate ranking is deterministic.
    5. The best next action is selected.
    6. None is returned when no valid work remains.
"""

from core.models.action import Action

from core.models.action_type import (
    ActionType,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.explorer.action_filter import (
    ActionFilter,
)

from agent.strategy.action.action_selector import (
    ActionSelector,
)

from agent.strategy.action.deterministic_action_strategy import (
    DeterministicActionStrategy,
)


class ControlledActionFilter(
    ActionFilter
):
    """
    Controlled policy for isolated action-selection tests.

    The close button is intentionally blocked.
    """

    def allow(
        self,
        action,
    ) -> bool:
        """
        Allow every action except closeButton.
        """

        return action.target != "closeButton"


def create_actions() -> list[Action]:
    """
    Create the controlled action set.

    The actions are intentionally not supplied in expected ranking order.
    """

    return [
        Action(
            action_type=ActionType.CLICK,
            target="plusButton",
        ),
        Action(
            action_type=ActionType.CLICK,
            target="num8Button",
        ),
        Action(
            action_type=ActionType.CLICK,
            target="closeButton",
        ),
        Action(
            action_type=ActionType.CLICK,
            target="num7Button",
        ),
    ]


def create_selector():
    """
    Create the common controlled test fixture.
    """

    state_hash = "state_hash_1"

    actions = create_actions()

    memory = ExplorationMemory()

    # num7Button has already been explored from this state.
    memory.mark_executed(
        state_hash,
        "num7Button",
    )

    action_filter = ControlledActionFilter()

    strategy = DeterministicActionStrategy()

    selector = ActionSelector(
        memory=memory,
        action_filter=action_filter,
        strategy=strategy,
    )

    return (
        selector,
        memory,
        state_hash,
        actions,
    )


def test_executed_action_is_not_candidate() -> None:
    """
    num7Button was already executed and must be excluded.
    """

    (
        selector,
        _,
        state_hash,
        actions,
    ) = create_selector()

    candidates = selector.get_candidates(
        state_hash,
        actions,
    )

    candidate_targets = [
        action.target
        for action in candidates
    ]

    assert "num7Button" not in candidate_targets


def test_blocked_action_is_not_candidate() -> None:
    """
    closeButton is blocked by ActionFilter and must be excluded.
    """

    (
        selector,
        _,
        state_hash,
        actions,
    ) = create_selector()

    candidates = selector.get_candidates(
        state_hash,
        actions,
    )

    candidate_targets = [
        action.target
        for action in candidates
    ]

    assert "closeButton" not in candidate_targets


def test_valid_candidates_are_correct() -> None:
    """
    Only num8Button and plusButton should remain valid.
    """

    (
        selector,
        _,
        state_hash,
        actions,
    ) = create_selector()

    candidates = selector.get_candidates(
        state_hash,
        actions,
    )

    candidate_targets = {
        action.target
        for action in candidates
    }

    assert candidate_targets == {
        "num8Button",
        "plusButton",
    }


def test_action_ranking_is_correct() -> None:
    """
    Both remaining actions have the same ActionType.

    Therefore target name becomes the deterministic tie-breaker.
    """

    (
        selector,
        _,
        state_hash,
        actions,
    ) = create_selector()

    ranked_actions = selector.rank_actions(
        state_hash,
        actions,
    )

    ranked_targets = [
        action.target
        for action in ranked_actions
    ]

    assert ranked_targets == [
        "num8Button",
        "plusButton",
    ]


def test_next_action_selection_is_correct() -> None:
    """
    num8Button must be selected as the highest-ranked valid action.
    """

    (
        selector,
        _,
        state_hash,
        actions,
    ) = create_selector()

    selected_action = (
        selector.select_next_action(
            state_hash,
            actions,
        )
    )

    assert selected_action is not None

    assert (
        selected_action.target
        ==
        "num8Button"
    )


def test_returns_none_when_no_valid_action_remains() -> None:
    """
    The selector must return None when every eligible action has
    already been executed.
    """

    (
        selector,
        memory,
        state_hash,
        actions,
    ) = create_selector()

    for action in actions:

        memory.mark_executed(
            state_hash,
            action.target,
        )

    selected_action = (
        selector.select_next_action(
            state_hash,
            actions,
        )
    )

    assert selected_action is None


def main() -> None:
    """
    Run all tests directly without requiring pytest.
    """

    tests = [
        test_executed_action_is_not_candidate,
        test_blocked_action_is_not_candidate,
        test_valid_candidates_are_correct,
        test_action_ranking_is_correct,
        test_next_action_selection_is_correct,
        test_returns_none_when_no_valid_action_remains,
    ]

    print()
    print(
        "===== ACTION SELECTOR TESTS ====="
    )
    print()

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()
    print(
        "All ActionSelector tests passed successfully."
    )


if __name__ == "__main__":

    main()