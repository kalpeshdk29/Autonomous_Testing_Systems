"""
File:
    test_checkpoint_manager.py

Purpose:
    Verify checkpoint lifecycle behavior independently from the
    filesystem and exploration coordinator.

What These Tests Prove:

    1. New sessions receive a creation timestamp.

    2. Existing session creation timestamps are preserved.

    3. Snapshot construction uses live graph and memory objects.

    4. create_snapshot() does not persist.

    5. checkpoint() persists exactly one snapshot.

    6. Checkpoint timestamps advance.

    7. created_at never changes between checkpoints.

    8. Live graph changes appear in later checkpoints.

    9. Live memory changes appear in later checkpoints.

    10. Failed saves do not update last_checkpoint_at.

    11. Invalid session IDs are rejected.

    12. Invalid root state IDs are rejected.

    13. Missing root states are rejected.
"""

from datetime import datetime

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.failure.failure_store import (
    FailureStore,
)

from agent.failure.failure_type import (
    FailureType,
)

from agent.persistence.session_status import (
    SessionStatus,
)

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

from agent.memory.exploration_memory import (
    ExplorationMemory,
)

from agent.persistence.checkpoint_manager import (
    CheckpointManager,
)

from agent.persistence.session_serializer import (
    SessionSerializer,
)


# =============================================================
# TEST DOUBLES
# =============================================================


class FakeClock:
    """
    Deterministic clock returning predefined timestamps.
    """

    def __init__(
        self,
        timestamps,
    ):
        self.timestamps = list(
            timestamps
        )

        self.index = 0

    def __call__(
        self,
    ):
        if self.index >= len(
            self.timestamps
        ):

            raise AssertionError(
                "FakeClock has no remaining timestamps."
            )

        value = self.timestamps[
            self.index
        ]

        self.index += 1

        return value


class RecordingRepository:
    """
    Repository test double recording saved snapshots.
    """

    def __init__(
        self,
    ):
        self.saved_snapshots = []

    def save(
        self,
        snapshot,
    ):
        self.saved_snapshots.append(
            snapshot
        )

        return (
            f"/fake/{snapshot.session_id}/session.json"
        )


class FailingRepository:
    """
    Repository test double that always fails.
    """

    def save(
        self,
        snapshot,
    ):
        raise RuntimeError(
            "Simulated persistence failure."
        )


# =============================================================
# FIXTURE HELPERS
# =============================================================


def create_action(
    action_id: str,
    target: str,
) -> Action:
    """
    Create a deterministic action.
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
    actions=None,
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
            10,
            0,
            0,
        ),

        window_title=(
            "Checkpoint Test Application"
        ),

        controls=[],

        values={
            "state": state_id,
        },

        available_actions=(
            actions
            or []
        ),

        screenshot_path=None,

        metadata={
            "fixture": True,
        },

        state_hash=state_hash,
    )


def create_runtime():
    """
    Create a small live graph and memory.
    """

    action_a = create_action(
        "action-A",
        "buttonA",
    )

    root_state = create_state(
        "S0",
        "hash-S0",
        [
            action_a,
        ],
    )

    graph = StateGraph()

    graph.add_state(
        root_state,
        depth=0,
    )

    memory = ExplorationMemory()

    return (
        graph,
        memory,
        action_a,
    )


def create_manager(
    clock,
    repository=None,
    created_at=None,
    status: SessionStatus = SessionStatus.CREATED,
    failure_store=None,
):
    """
    Create a standard checkpoint manager fixture.
    """

    graph, memory, action = (
        create_runtime()
    )

    if repository is None:

        repository = (
            RecordingRepository()
        )

    manager = CheckpointManager(
        session_id="session-123",

        root_state_id="S0",

        graph=graph,

        memory=memory,

        repository=repository,

        created_at=created_at,

        status=status,

        clock=clock,
        
        failure_store=(
            failure_store
        ),
    )

    return (
        manager,
        graph,
        memory,
        action,
        repository,
    )

def create_failure(
    failure_id: str,
    source_state_id: str,
    action: Action,
) -> FailureRecord:
    """
    Create a deterministic failure for checkpoint tests.
    """

    return FailureRecord(
        failure_id=failure_id,

        failure_type=(
            FailureType
            .ACTION_EXECUTION_FAILED
        ),

        message=(
            "The selected action could "
            "not be executed."
        ),

        timestamp=datetime(
            2026,
            7,
            10,
            15,
            0,
            0,
        ),

        source_state_id=(
            source_state_id
        ),

        action=action,

        target_state_id=None,

        replay_path=[],

        screenshot_path=None,

        recoverable=True,

        metadata={
            "fixture": True,
        },
    )

# =============================================================
# SESSION LIFECYCLE TESTS
# =============================================================


def test_new_manager_defaults_to_created():
    """
    New checkpoint managers must begin in CREATED state.
    """

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),
            ]
        )
    )

    assert (
        manager.status
        ==
        SessionStatus.CREATED
    )


def test_existing_session_status_is_preserved():
    """
    Resumed sessions must preserve their loaded lifecycle status.
    """

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    12,
                    0,
                    0,
                ),
            ]
        ),

        created_at=datetime(
            2026,
            7,
            4,
            9,
            0,
            0,
        ),

        status=SessionStatus.RUNNING,
    )

    assert (
        manager.status
        ==
        SessionStatus.RUNNING
    )

    snapshot = manager.checkpoint()

    assert (
        snapshot.status
        ==
        SessionStatus.RUNNING
    )


def test_mark_running_persists_running_status():
    """
    mark_running() must durably persist RUNNING.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    running_at = datetime(
        2026,
        7,
        5,
        10,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,
                running_at,
            ]
        )
    )

    snapshot = manager.mark_running()

    assert (
        manager.status
        ==
        SessionStatus.RUNNING
    )

    assert (
        snapshot.status
        ==
        SessionStatus.RUNNING
    )

    assert len(
        repository.saved_snapshots
    ) == 1

    assert (
        repository.saved_snapshots[-1].status
        ==
        SessionStatus.RUNNING
    )


def test_normal_checkpoints_preserve_running_status():
    """
    Automatic checkpoints during exploration must remain RUNNING.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    running_at = datetime(
        2026,
        7,
        5,
        10,
        0,
        0,
    )

    checkpoint_at = datetime(
        2026,
        7,
        5,
        11,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,
                running_at,
                checkpoint_at,
            ]
        )
    )

    manager.mark_running()

    snapshot = manager.checkpoint()

    assert (
        snapshot.status
        ==
        SessionStatus.RUNNING
    )

    assert (
        repository.saved_snapshots[-1].status
        ==
        SessionStatus.RUNNING
    )

    assert len(
        repository.saved_snapshots
    ) == 2


def test_mark_completed_persists_completed_status():
    """
    mark_completed() must durably persist clean completion.
    """

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    10,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    12,
                    0,
                    0,
                ),
            ]
        )
    )

    manager.mark_running()

    snapshot = manager.mark_completed()

    assert (
        manager.status
        ==
        SessionStatus.COMPLETED
    )

    assert (
        snapshot.status
        ==
        SessionStatus.COMPLETED
    )

    assert (
        repository.saved_snapshots[-1].status
        ==
        SessionStatus.COMPLETED
    )


def test_mark_failed_persists_failed_status():
    """
    mark_failed() must durably persist terminal failure.
    """

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    10,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    12,
                    0,
                    0,
                ),
            ]
        )
    )

    manager.mark_running()

    snapshot = manager.mark_failed()

    assert (
        manager.status
        ==
        SessionStatus.FAILED
    )

    assert (
        snapshot.status
        ==
        SessionStatus.FAILED
    )

    assert (
        repository.saved_snapshots[-1].status
        ==
        SessionStatus.FAILED
    )


def test_running_snapshot_represents_interruption():
    """
    A persisted RUNNING checkpoint must be detectable as an
    interrupted previous execution when loaded later.
    """

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    10,
                    0,
                    0,
                ),
            ]
        )
    )

    snapshot = manager.mark_running()

    assert snapshot.was_interrupted

def test_failed_mark_running_does_not_update_last_checkpoint():
    """
    Failed RUNNING persistence must not be reported as a successful
    durable checkpoint.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    running_at = datetime(
        2026,
        7,
        5,
        10,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,
                running_at,
            ]
        ),

        repository=(
            FailingRepository()
        ),
    )

    try:

        manager.mark_running()

        assert False, (
            "Expected persistence failure."
        )

    except RuntimeError:

        pass

    assert (
        manager.last_checkpoint_at
        is None
    )


def test_invalid_status_is_rejected():
    """
    CheckpointManager must accept only SessionStatus values.
    """

    graph, memory, _ = (
        create_runtime()
    )

    try:

        CheckpointManager(
            session_id="session-123",

            root_state_id="S0",

            graph=graph,

            memory=memory,

            repository=(
                RecordingRepository()
            ),

            status="RUNNING",
        )

        assert False, (
            "Expected invalid status "
            "to be rejected."
        )

    except ValueError as error:

        assert "status" in str(error)


# =============================================================
# FAILURE STORE CHECKPOINT TESTS
# =============================================================


def test_snapshot_without_failure_store_has_empty_failures():
    """
    Failure persistence must remain optional for backward
    compatibility.
    """

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    10,
                    9,
                    0,
                    0,
                ),
            ]
        )
    )

    snapshot = (
        manager.create_snapshot(
            updated_at=datetime(
                2026,
                7,
                10,
                10,
                0,
                0,
            )
        )
    )

    assert snapshot.failures == []


def test_snapshot_captures_current_failure_store():
    """
    Snapshot construction must capture the current structured
    failure history.
    """

    failure_store = FailureStore()

    (
        manager,
        _,
        _,
        action,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    10,
                    9,
                    0,
                    0,
                ),
            ]
        ),

        failure_store=(
            failure_store
        ),
    )

    failure = create_failure(
        failure_id="failure-1",

        source_state_id="S0",

        action=action,
    )

    failure_store.add(
        failure
    )

    snapshot = (
        manager.create_snapshot(
            updated_at=datetime(
                2026,
                7,
                10,
                10,
                0,
                0,
            )
        )
    )

    assert len(
        snapshot.failures
    ) == 1

    assert (
        snapshot.failures[0]
        is
        failure
    )


def test_live_failure_changes_appear_in_later_checkpoint():
    """
    Later checkpoints must observe failures added after an earlier
    checkpoint.

    This proves CheckpointManager reads the live FailureStore
    instead of caching failure history during construction.
    """

    failure_store = FailureStore()

    (
        manager,
        _,
        _,
        action,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    10,
                    9,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    10,
                    10,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    10,
                    11,
                    0,
                    0,
                ),
            ]
        ),

        failure_store=(
            failure_store
        ),
    )

    manager.checkpoint()

    assert (
        repository
        .saved_snapshots[0]
        .failures
        ==
        []
    )

    failure_store.add(
        create_failure(
            failure_id="failure-1",

            source_state_id="S0",

            action=action,
        )
    )

    manager.checkpoint()

    latest_snapshot = (
        repository
        .saved_snapshots[-1]
    )

    assert len(
        latest_snapshot.failures
    ) == 1

    assert (
        latest_snapshot
        .failures[0]
        .failure_id
        ==
        "failure-1"
    )


def test_multiple_failures_preserve_order_in_checkpoint():
    """
    Checkpoints must preserve detector discovery order.
    """

    failure_store = FailureStore()

    (
        manager,
        _,
        _,
        action,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    10,
                    9,
                    0,
                    0,
                ),
            ]
        ),

        failure_store=(
            failure_store
        ),
    )

    failure_store.add(
        create_failure(
            failure_id="failure-1",

            source_state_id="S0",

            action=action,
        )
    )

    failure_store.add(
        create_failure(
            failure_id="failure-2",

            source_state_id="S1",

            action=action,
        )
    )

    snapshot = (
        manager.create_snapshot(
            updated_at=datetime(
                2026,
                7,
                10,
                10,
                0,
                0,
            )
        )
    )

    assert [
        failure.failure_id

        for failure
        in snapshot.failures
    ] == [
        "failure-1",
        "failure-2",
    ]

# =============================================================
# TESTS
# =============================================================


def test_new_session_receives_creation_timestamp():
    """
    New managers must obtain created_at from the clock.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    clock = FakeClock(
        [
            created_at,
        ]
    )

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=clock
    )

    assert (
        manager.created_at
        ==
        created_at
    )


def test_existing_creation_timestamp_is_preserved():
    """
    Resumed sessions must preserve original created_at.

    The clock must not be consumed during initialization when an
    existing creation timestamp is supplied.
    """

    original_created_at = datetime(
        2026,
        7,
        4,
        8,
        0,
        0,
    )

    checkpoint_time = datetime(
        2026,
        7,
        5,
        12,
        0,
        0,
    )

    clock = FakeClock(
        [
            checkpoint_time,
        ]
    )

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=clock,
        created_at=original_created_at,
    )

    snapshot = manager.checkpoint()

    assert (
        snapshot.created_at
        ==
        original_created_at
    )

    assert (
        snapshot.updated_at
        ==
        checkpoint_time
    )


def test_snapshot_uses_live_graph_and_memory():
    """
    Snapshot construction must reference the current runtime.
    """

    snapshot_time = datetime(
        2026,
        7,
        5,
        12,
        0,
        0,
    )

    (
        manager,
        graph,
        memory,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),
            ]
        )
    )

    snapshot = (
        manager.create_snapshot(
            updated_at=snapshot_time
        )
    )

    assert snapshot.graph is graph

    assert snapshot.memory is memory

    assert (
        snapshot.root_state_id
        ==
        "S0"
    )

    assert (
        snapshot.session_id
        ==
        "session-123"
    )

    assert (
        snapshot.schema_version
        ==
        SessionSerializer
        .CURRENT_SCHEMA_VERSION
    )

    assert (
    snapshot.status
    ==
    SessionStatus.CREATED
    )


def test_create_snapshot_does_not_persist():
    """
    Snapshot construction alone must not call the repository.
    """

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),
            ]
        )
    )

    manager.create_snapshot(
        updated_at=datetime(
            2026,
            7,
            5,
            12,
            0,
            0,
        )
    )

    assert (
        repository.saved_snapshots
        ==
        []
    )


def test_checkpoint_persists_exactly_one_snapshot():
    """
    One checkpoint call must perform one repository save.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    checkpoint_time = datetime(
        2026,
        7,
        5,
        12,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,
                checkpoint_time,
            ]
        )
    )

    snapshot = manager.checkpoint()

    assert len(
        repository.saved_snapshots
    ) == 1

    assert (
        repository.saved_snapshots[0]
        is snapshot
    )

    assert (
        manager.last_checkpoint_at
        ==
        checkpoint_time
    )


def test_checkpoint_timestamps_advance():
    """
    Each successful checkpoint must receive a new updated_at.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    first_checkpoint = datetime(
        2026,
        7,
        5,
        10,
        0,
        0,
    )

    second_checkpoint = datetime(
        2026,
        7,
        5,
        11,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,
                first_checkpoint,
                second_checkpoint,
            ]
        )
    )

    snapshot_1 = manager.checkpoint()

    snapshot_2 = manager.checkpoint()

    assert (
        snapshot_1.updated_at
        ==
        first_checkpoint
    )

    assert (
        snapshot_2.updated_at
        ==
        second_checkpoint
    )

    assert (
        manager.last_checkpoint_at
        ==
        second_checkpoint
    )

    assert len(
        repository.saved_snapshots
    ) == 2


def test_created_at_never_changes_between_checkpoints():
    """
    Session creation time must remain stable.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,

                datetime(
                    2026,
                    7,
                    5,
                    10,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    11,
                    0,
                    0,
                ),
            ]
        )
    )

    snapshot_1 = manager.checkpoint()

    snapshot_2 = manager.checkpoint()

    assert (
        snapshot_1.created_at
        ==
        created_at
    )

    assert (
        snapshot_2.created_at
        ==
        created_at
    )


def test_live_graph_changes_appear_in_later_checkpoint():
    """
    Later checkpoints must observe graph mutations.
    """

    (
        manager,
        graph,
        _,
        action,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    10,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    11,
                    0,
                    0,
                ),
            ]
        )
    )

    manager.checkpoint()

    state_1 = create_state(
        "S1",
        "hash-S1",
    )

    graph.add_state(
        state_1,
        depth=1,
    )

    graph.add_transition(
        source_id="S0",
        action=action,
        target_id="S1",
        success=True,
        duration=1.0,
    )

    manager.checkpoint()

    latest_snapshot = (
        repository.saved_snapshots[-1]
    )

    assert len(
        latest_snapshot.graph.states
    ) == 2


def test_live_memory_changes_appear_in_later_checkpoint():
    """
    Later checkpoints must observe memory mutations.
    """

    (
        manager,
        _,
        memory,
        _,
        repository,
    ) = create_manager(
        clock=FakeClock(
            [
                datetime(
                    2026,
                    7,
                    5,
                    9,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    10,
                    0,
                    0,
                ),

                datetime(
                    2026,
                    7,
                    5,
                    11,
                    0,
                    0,
                ),
            ]
        )
    )

    manager.checkpoint()

    memory.mark_executed(
        "hash-S0",
        "buttonA",
    )

    manager.checkpoint()

    latest_snapshot = (
        repository.saved_snapshots[-1]
    )

    assert (
        latest_snapshot.memory.is_executed(
            "hash-S0",
            "buttonA",
        )
    )


def test_failed_save_does_not_update_last_checkpoint():
    """
    Failed persistence must not be reported as a checkpoint.
    """

    created_at = datetime(
        2026,
        7,
        5,
        9,
        0,
        0,
    )

    failed_checkpoint_time = datetime(
        2026,
        7,
        5,
        10,
        0,
        0,
    )

    (
        manager,
        _,
        _,
        _,
        _,
    ) = create_manager(
        clock=FakeClock(
            [
                created_at,
                failed_checkpoint_time,
            ]
        ),

        repository=(
            FailingRepository()
        ),
    )

    try:

        manager.checkpoint()

        assert False, (
            "Expected persistence failure."
        )

    except RuntimeError as error:

        assert (
            "Simulated persistence failure"
            in str(error)
        )

    assert (
        manager.last_checkpoint_at
        is None
    )


def test_invalid_session_ids_are_rejected():
    """
    Session identity must be valid.
    """

    graph, memory, _ = (
        create_runtime()
    )

    invalid_ids = [
        "",
        "   ",
        None,
    ]

    for session_id in invalid_ids:

        try:

            CheckpointManager(
                session_id=session_id,

                root_state_id="S0",

                graph=graph,

                memory=memory,

                repository=(
                    RecordingRepository()
                ),
            )

            assert False, (
                "Expected invalid session_id "
                f"to be rejected: {session_id}"
            )

        except ValueError:

            pass


def test_invalid_root_state_ids_are_rejected():
    """
    Root identity must be a non-empty string.
    """

    graph, memory, _ = (
        create_runtime()
    )

    invalid_ids = [
        "",
        "   ",
        None,
    ]

    for root_state_id in invalid_ids:

        try:

            CheckpointManager(
                session_id="session-123",

                root_state_id=(
                    root_state_id
                ),

                graph=graph,

                memory=memory,

                repository=(
                    RecordingRepository()
                ),
            )

            assert False, (
                "Expected invalid root_state_id "
                "to be rejected."
            )

        except ValueError:

            pass


def test_missing_root_state_is_rejected():
    """
    The persisted replay root must exist in the live graph.
    """

    graph, memory, _ = (
        create_runtime()
    )

    try:

        CheckpointManager(
            session_id="session-123",

            root_state_id="missing-state",

            graph=graph,

            memory=memory,

            repository=(
                RecordingRepository()
            ),
        )

        assert False, (
            "Expected missing root state "
            "to be rejected."
        )

    except ValueError as error:

        assert (
            "does not exist"
            in str(error)
        )


# =============================================================
# DIRECT TEST RUNNER
# =============================================================


def main():
    """
    Run all tests directly without pytest.
    """

    tests = [
        test_new_session_receives_creation_timestamp,
        test_existing_creation_timestamp_is_preserved,
        test_snapshot_uses_live_graph_and_memory,
        test_create_snapshot_does_not_persist,
        test_checkpoint_persists_exactly_one_snapshot,
        test_checkpoint_timestamps_advance,
        test_created_at_never_changes_between_checkpoints,
        test_live_graph_changes_appear_in_later_checkpoint,
        test_live_memory_changes_appear_in_later_checkpoint,
        test_failed_save_does_not_update_last_checkpoint,

        test_new_manager_defaults_to_created,
        test_existing_session_status_is_preserved,
        test_mark_running_persists_running_status,
        test_normal_checkpoints_preserve_running_status,
        test_mark_completed_persists_completed_status,
        test_mark_failed_persists_failed_status,
        test_running_snapshot_represents_interruption,
        test_failed_mark_running_does_not_update_last_checkpoint,
        test_invalid_status_is_rejected,
        test_snapshot_without_failure_store_has_empty_failures,
        test_snapshot_captures_current_failure_store,
        test_live_failure_changes_appear_in_later_checkpoint,
        test_multiple_failures_preserve_order_in_checkpoint,
        test_invalid_session_ids_are_rejected,
        test_invalid_root_state_ids_are_rejected,
        test_missing_root_state_is_rejected,
    ]

    print()

    print(
        "===== CHECKPOINT MANAGER TESTS ====="
    )

    print()

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All CheckpointManager tests "
        "passed successfully."
    )


if __name__ == "__main__":

    main()