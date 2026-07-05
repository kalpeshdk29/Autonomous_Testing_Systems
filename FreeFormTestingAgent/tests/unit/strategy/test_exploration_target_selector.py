"""
Unit tests for ExplorationTargetSelector.

Controlled scenario:

    S0
        depth = 0
        unexplored eligible actions = 0
        fully explored
        expected: excluded

    S1
        depth = 1
        unexplored eligible actions = 2
        expected: valid candidate

    S2
        depth = 1
        unexplored eligible actions = 4
        expected: valid candidate and highest priority

    S3
        depth = 2
        unexplored eligible actions = 5
        max_depth = 2
        expected: excluded because it cannot be expanded

Expected candidates:
    S1
    S2

Expected ranking:
    S2
    S1

Expected selection:
    S2
"""

from dataclasses import dataclass

from agent.strategy.exploration_target_selector import (
    ExplorationTargetSelector,
)
from agent.strategy.shallowest_first_strategy import (
    ShallowestFirstStrategy,
)


@dataclass
class FakeStateCoverage:
    """
    Minimal controlled replacement for the real StateCoverage model.

    The selector only needs these fields for this isolated unit test.
    """

    state_id: str
    state_hash: str
    depth: int
    eligible_unexplored_actions: int


class FakeCoverageReport:
    """
    Controlled replacement for CoverageReport.

    It reproduces the selector-facing behavior of the real report without
    depending on StateGraph, ExplorationMemory, or ActionFilter.
    """

    def __init__(
        self,
        state_coverages: list[FakeStateCoverage],
    ) -> None:
        self.state_coverages = state_coverages

    def get_states_with_unexplored_eligible_actions(
        self,
    ) -> list[FakeStateCoverage]:
        """
        Return only states containing remaining eligible exploration work.
        """

        return [
            state_coverage
            for state_coverage in self.state_coverages
            if state_coverage.eligible_unexplored_actions > 0
        ]


class FakeCoverageEngine:
    """
    Controlled replacement for CoverageEngine.
    """

    def __init__(self, report: FakeCoverageReport) -> None:
        self.report = report

    def get_states_with_unexplored_eligible_actions(
        self,
    ) -> list[FakeStateCoverage]:
        """
        Match the real CoverageEngine query API.
        """

        return (
            self.report
            .get_states_with_unexplored_eligible_actions()
        )


def create_selector() -> ExplorationTargetSelector:
    """
    Build the common controlled test fixture.
    """

    state_coverages = [
        FakeStateCoverage(
            state_id="S0",
            state_hash="hash_s0",
            depth=0,
            eligible_unexplored_actions=0,
        ),
        FakeStateCoverage(
            state_id="S1",
            state_hash="hash_s1",
            depth=1,
            eligible_unexplored_actions=2,
        ),
        FakeStateCoverage(
            state_id="S2",
            state_hash="hash_s2",
            depth=1,
            eligible_unexplored_actions=4,
        ),
        FakeStateCoverage(
            state_id="S3",
            state_hash="hash_s3",
            depth=2,
            eligible_unexplored_actions=5,
        ),
    ]

    coverage_report = FakeCoverageReport(state_coverages)

    coverage_engine = FakeCoverageEngine(coverage_report)

    strategy = ShallowestFirstStrategy()

    return ExplorationTargetSelector(
        coverage_engine=coverage_engine,
        strategy=strategy,
        max_depth=2,
    )


def test_completed_state_is_not_candidate() -> None:
    """
    S0 has no remaining eligible actions and must not become a candidate.
    """

    selector = create_selector()

    candidates = selector.get_candidates()

    candidate_ids = [
        candidate.state_id
        for candidate in candidates
    ]

    assert "S0" not in candidate_ids


def test_max_depth_state_is_not_candidate() -> None:
    """
    S3 is stored at depth 2, but max_depth=2 means it cannot be expanded.
    """

    selector = create_selector()

    candidates = selector.get_candidates()

    candidate_ids = [
        candidate.state_id
        for candidate in candidates
    ]

    assert "S3" not in candidate_ids


def test_valid_candidates_are_correct() -> None:
    """
    Only S1 and S2 satisfy both coverage and depth constraints.
    """

    selector = create_selector()

    candidates = selector.get_candidates()

    candidate_ids = [
        candidate.state_id
        for candidate in candidates
    ]

    assert candidate_ids == ["S1", "S2"]


def test_target_ranking_is_correct() -> None:
    """
    S1 and S2 have equal depth.

    S2 must rank first because it has more unexplored eligible actions.
    """

    selector = create_selector()

    ranked_targets = selector.rank_targets()

    ranked_ids = [
        target.state_id
        for target in ranked_targets
    ]

    assert ranked_ids == ["S2", "S1"]


def test_next_target_selection_is_correct() -> None:
    """
    The selector must return S2 as the best next exploration target.
    """

    selector = create_selector()

    selected_target = selector.select_next_target()

    assert selected_target is not None
    assert selected_target.state_id == "S2"
    assert selected_target.state_hash == "hash_s2"
    assert selected_target.depth == 1
    assert selected_target.unexplored_eligible_actions == 4


def main() -> None:
    """
    Run all tests directly without requiring pytest.
    """

    tests = [
        test_completed_state_is_not_candidate,
        test_max_depth_state_is_not_candidate,
        test_valid_candidates_are_correct,
        test_target_ranking_is_correct,
        test_next_target_selection_is_correct,
    ]

    print("\n===== EXPLORATION TARGET SELECTOR TESTS =====\n")

    for test in tests:
        test()

        print(f"PASS: {test.__name__}")

    print(
        "\nAll ExplorationTargetSelector tests passed successfully."
    )


if __name__ == "__main__":
    main()