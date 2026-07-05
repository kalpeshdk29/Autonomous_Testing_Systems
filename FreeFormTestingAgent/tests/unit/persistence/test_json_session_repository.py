"""
File:
    test_json_session_repository.py

Purpose:
    Verify real filesystem persistence of complete exploration
    sessions.

What These Tests Prove:

    1. save() creates the expected storage structure.

    2. session.json contains valid formatted JSON.

    3. load() reconstructs the complete session.

    4. Graph knowledge survives disk persistence.

    5. ExplorationMemory survives disk persistence.

    6. Coverage is identical before and after disk persistence.

    7. Saving again replaces the previous snapshot.

    8. Successful saves leave no temporary file.

    9. exists() reports persisted sessions correctly.

    10. list_sessions() returns only real session files.

    11. Missing sessions raise FileNotFoundError.

    12. Invalid JSON is rejected.

    13. Unsupported schema versions are rejected.

    14. Unsafe session IDs are rejected.
"""

import json
import tempfile

from datetime import datetime
from pathlib import Path

from core.graph.state_graph import (
    StateGraph,
)

from core.models.action import (
    Action,
)

from core.models.action_type import (
    ActionType,
)

from core.models.state import (
    ApplicationState,
)

from agent.coverage.coverage_engine import (
    CoverageEngine,
)

from agent.explorer.action_filter import (
    ActionFilter,
)

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.persistence.json_session_repository import (
    JsonSessionRepository,
)

from agent.persistence.session_serializer import (
    SessionSerializer,
)

from agent.persistence.session_snapshot import (
    ExplorationSessionSnapshot,
)


class RepositoryTestActionFilter(
    ActionFilter
):
    """
    Controlled eligible-action policy.
    """

    ALLOWED_TARGETS = {
        "buttonA",
        "buttonB",
        "buttonC",
    }

    def allow(
        self,
        action,
    ) -> bool:

        return (
            action.target
            in
            self.ALLOWED_TARGETS
        )


def create_action(
    action_id: str,
    target: str,
) -> Action:
    """
    Create a deterministic CLICK action.
    """

    return Action(
        action_id=action_id,
        action_type=ActionType.CLICK,
        target=target,
        value=None,
        timestamp=datetime(
            2026,
            7,
            5,
            10,
            0,
            0,
        ),
        description=f"Click {target}",
    )


def create_state(
    state_id: str,
    state_hash: str,
    available_actions=None,
) -> ApplicationState:
    """
    Create a deterministic application state.
    """

    return ApplicationState(
        state_id=state_id,
        timestamp=datetime(
            2026,
            7,
            5,
            11,
            0,
            0,
        ),
        window_title="Test Application",
        controls=[],
        values={
            "state": state_id,
        },
        available_actions=(
            available_actions
            or []
        ),
        screenshot_path=(
            f"screenshots/{state_id}.png"
        ),
        metadata={
            "fixture": True,
        },
        state_hash=state_hash,
    )


def create_test_snapshot(
    session_id="session-123",
) -> ExplorationSessionSnapshot:
    """
    Create a deterministic complete session.
    """

    action_a = create_action(
        "action-A",
        "buttonA",
    )

    action_b = create_action(
        "action-B",
        "buttonB",
    )

    action_c = create_action(
        "action-C",
        "buttonC",
    )

    state_0 = create_state(
        "S0",
        "hash-S0",
        [
            action_a,
            action_b,
        ],
    )

    state_1 = create_state(
        "S1",
        "hash-S1",
        [
            action_c,
        ],
    )

    graph = StateGraph()

    graph.add_state(
        state_0,
        depth=0,
    )

    graph.add_state(
        state_1,
        depth=1,
    )

    graph.add_transition(
        source_id="S0",
        action=action_a,
        target_id="S1",
        success=True,
        duration=1.25,
    )

    memory = ExplorationMemory()

    memory.mark_executed(
        "hash-S0",
        "buttonA",
    )

    return ExplorationSessionSnapshot(
        schema_version=(
            SessionSerializer
            .CURRENT_SCHEMA_VERSION
        ),

        session_id=session_id,

        root_state_id="S0",

        created_at=datetime(
            2026,
            7,
            5,
            9,
            0,
            0,
        ),

        updated_at=datetime(
            2026,
            7,
            5,
            12,
            30,
            45,
        ),

        graph=graph,

        memory=memory,
    )


def create_repository(
    temporary_directory,
):
    """
    Create a repository inside an isolated temporary root.
    """

    storage_root = (
        Path(temporary_directory)
        /
        "storage"
        /
        "database"
        /
        "sessions"
    )

    return JsonSessionRepository(
        storage_root=storage_root
    )


def get_coverage_values(
    graph,
    memory,
):
    """
    Return stable eligible-coverage values.
    """

    coverage_engine = CoverageEngine(
        graph=graph,
        memory=memory,
        action_filter=(
            RepositoryTestActionFilter()
        ),
    )

    report = (
        coverage_engine.calculate_report()
    )

    return {
        "total_states": (
            report.total_states
        ),

        "eligible_total_actions": (
            report.eligible_total_actions
        ),

        "eligible_explored_actions": (
            report.eligible_explored_actions
        ),

        "eligible_unexplored_actions": (
            report.eligible_unexplored_actions
        ),

        "eligible_action_coverage_percentage": (
            report
            .eligible_action_coverage_percentage
        ),
    }


def test_save_creates_expected_storage_structure():
    """
    save() must create:

        storage/database/sessions/
            session-123/
                session.json
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        snapshot = create_test_snapshot()

        saved_path = repository.save(
            snapshot
        )

        expected_path = (
            Path(temp)
            /
            "storage"
            /
            "database"
            /
            "sessions"
            /
            "session-123"
            /
            "session.json"
        )

        assert saved_path == expected_path

        assert expected_path.is_file()


def test_saved_file_contains_valid_json():
    """
    Persisted session.json must contain valid JSON.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        repository.save(
            create_test_snapshot()
        )

        session_file = (
            repository.storage_root
            /
            "session-123"
            /
            "session.json"
        )

        with session_file.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        assert (
            data["schema_version"]
            ==
            SessionSerializer.CURRENT_SCHEMA_VERSION
        )

        assert (
            data["session"]["session_id"]
            ==
            "session-123"
        )


def test_disk_round_trip_preserves_session():
    """
    Complete session metadata must survive real disk persistence.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        original = create_test_snapshot()

        repository.save(
            original
        )

        restored = repository.load(
            "session-123"
        )

        assert (
            restored.session_id
            ==
            original.session_id
        )

        assert (
            restored.root_state_id
            ==
            original.root_state_id
        )

        assert (
            restored.created_at
            ==
            original.created_at
        )

        assert (
            restored.updated_at
            ==
            original.updated_at
        )


def test_disk_round_trip_preserves_graph():
    """
    Loaded graph must preserve states, transitions, and paths.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        repository.save(
            create_test_snapshot()
        )

        restored = repository.load(
            "session-123"
        )

        assert len(
            restored.graph.states
        ) == 2

        assert (
            restored.graph.find_path(
                "S0",
                "S1",
            )
            ==
            [
                "S0",
                "S1",
            ]
        )

        assert (
            len(
                restored.graph.edges["S0"]
            )
            ==
            1
        )


def test_disk_round_trip_preserves_memory():
    """
    Loaded memory must preserve exploration history.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        repository.save(
            create_test_snapshot()
        )

        restored = repository.load(
            "session-123"
        )

        assert restored.memory.is_executed(
            "hash-S0",
            "buttonA",
        )

        assert not restored.memory.is_executed(
            "hash-S0",
            "buttonB",
        )


def test_coverage_is_identical_after_disk_round_trip():
    """
    Disk persistence must preserve decision-system knowledge.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        original = create_test_snapshot()

        coverage_before = (
            get_coverage_values(
                original.graph,
                original.memory,
            )
        )

        repository.save(
            original
        )

        restored = repository.load(
            "session-123"
        )

        coverage_after = (
            get_coverage_values(
                restored.graph,
                restored.memory,
            )
        )

        assert (
            coverage_after
            ==
            coverage_before
        )


def test_saving_again_replaces_previous_snapshot():
    """
    Saving the same session ID again must replace session.json.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        snapshot = create_test_snapshot()

        repository.save(
            snapshot
        )

        snapshot.memory.mark_executed(
            "hash-S0",
            "buttonB",
        )

        snapshot.updated_at = datetime(
            2026,
            7,
            5,
            13,
            0,
            0,
        )

        repository.save(
            snapshot
        )

        restored = repository.load(
            "session-123"
        )

        assert restored.memory.is_executed(
            "hash-S0",
            "buttonB",
        )

        assert (
            restored.updated_at
            ==
            snapshot.updated_at
        )


def test_successful_save_leaves_no_temp_file():
    """
    session.json.tmp must not remain after successful save.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        repository.save(
            create_test_snapshot()
        )

        temp_file = (
            repository.storage_root
            /
            "session-123"
            /
            "session.json.tmp"
        )

        assert not temp_file.exists()


def test_exists_reports_persisted_sessions():
    """
    exists() must distinguish stored and missing sessions.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        assert not repository.exists(
            "session-123"
        )

        repository.save(
            create_test_snapshot()
        )

        assert repository.exists(
            "session-123"
        )

        assert not repository.exists(
            "missing-session"
        )


def test_list_sessions_returns_only_stored_sessions():
    """
    list_sessions() must ignore unrelated directories.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        repository.save(
            create_test_snapshot(
                "session-B"
            )
        )

        repository.save(
            create_test_snapshot(
                "session-A"
            )
        )

        unrelated = (
            repository.storage_root
            /
            "not-a-session"
        )

        unrelated.mkdir(
            parents=True
        )

        assert (
            repository.list_sessions()
            ==
            [
                "session-A",
                "session-B",
            ]
        )


def test_missing_session_raises_file_not_found():
    """
    Loading an unknown session must fail clearly.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        try:

            repository.load(
                "missing-session"
            )

            assert False, (
                "Expected FileNotFoundError."
            )

        except FileNotFoundError as error:

            assert (
                "missing-session"
                in str(error)
            )


def test_invalid_json_is_rejected():
    """
    Corrupted JSON must not be silently accepted.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        session_directory = (
            repository.storage_root
            /
            "broken-session"
        )

        session_directory.mkdir(
            parents=True
        )

        session_file = (
            session_directory
            /
            "session.json"
        )

        session_file.write_text(
            "{ invalid json",
            encoding="utf-8",
        )

        try:

            repository.load(
                "broken-session"
            )

            assert False, (
                "Expected JSONDecodeError."
            )

        except json.JSONDecodeError:

            pass


def test_unsupported_schema_version_is_rejected():
    """
    Repository loading must preserve serializer validation.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        repository.save(
            create_test_snapshot()
        )

        session_file = (
            repository.storage_root
            /
            "session-123"
            /
            "session.json"
        )

        data = json.loads(
            session_file.read_text(
                encoding="utf-8"
            )
        )

        data[
            "schema_version"
        ] = 999

        session_file.write_text(
            json.dumps(
                data
            ),
            encoding="utf-8",
        )

        try:

            repository.load(
                "session-123"
            )

            assert False, (
                "Expected unsupported schema "
                "to raise ValueError."
            )

        except ValueError as error:

            assert (
                "Unsupported session schema version"
                in str(error)
            )


def test_unsafe_session_ids_are_rejected():
    """
    Session IDs must not escape the configured storage root.
    """

    with tempfile.TemporaryDirectory() as temp:

        repository = create_repository(
            temp
        )

        invalid_ids = [
            "",
            "   ",
            ".",
            "..",
            "../outside",
            "folder/session",
            "folder\\session",
        ]

        for session_id in invalid_ids:

            try:

                repository.exists(
                    session_id
                )

                assert False, (
                    "Expected invalid session_id "
                    f"to be rejected: {session_id}"
                )

            except ValueError:

                pass


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_save_creates_expected_storage_structure,
        test_saved_file_contains_valid_json,
        test_disk_round_trip_preserves_session,
        test_disk_round_trip_preserves_graph,
        test_disk_round_trip_preserves_memory,
        test_coverage_is_identical_after_disk_round_trip,
        test_saving_again_replaces_previous_snapshot,
        test_successful_save_leaves_no_temp_file,
        test_exists_reports_persisted_sessions,
        test_list_sessions_returns_only_stored_sessions,
        test_missing_session_raises_file_not_found,
        test_invalid_json_is_rejected,
        test_unsupported_schema_version_is_rejected,
        test_unsafe_session_ids_are_rejected,
    ]

    print()

    print(
        "===== JSON SESSION REPOSITORY TESTS ====="
    )

    print()

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All JsonSessionRepository tests passed successfully."
    )


if __name__ == "__main__":

    main()