"""
Unit tests for RecoveryContext.
"""

from agent.recovery.recovery_context import (
    RecoveryContext,
)


class Dummy:
    pass


def make_context():

    return RecoveryContext(
        executable="calc.exe",

        window_title="Calculator",

        ui_adapter=Dummy(),

        replay_engine=Dummy(),

        graph=Dummy(),

        memory=Dummy(),
    )


def test_context_preserves_executable():

    context = make_context()

    assert (
        context.executable
        ==
        "calc.exe"
    )


def test_context_preserves_window_title():

    context = make_context()

    assert (
        context.window_title
        ==
        "Calculator"
    )


def test_context_preserves_runtime_objects():

    context = make_context()

    assert context.ui_adapter is not None

    assert context.replay_engine is not None

    assert context.graph is not None

    assert context.memory is not None


def test_empty_executable_is_rejected():

    try:

        RecoveryContext(
            executable="",

            window_title="Calculator",

            ui_adapter=Dummy(),

            replay_engine=Dummy(),

            graph=Dummy(),

            memory=Dummy(),
        )

        assert False

    except ValueError:

        pass


def test_empty_window_title_is_rejected():

    try:

        RecoveryContext(
            executable="calc.exe",

            window_title="",

            ui_adapter=Dummy(),

            replay_engine=Dummy(),

            graph=Dummy(),

            memory=Dummy(),
        )

        assert False

    except ValueError:

        pass


def test_missing_ui_adapter_is_rejected():

    try:

        RecoveryContext(
            executable="calc.exe",

            window_title="Calculator",

            ui_adapter=None,

            replay_engine=Dummy(),

            graph=Dummy(),

            memory=Dummy(),
        )

        assert False

    except ValueError:

        pass


def test_missing_replay_engine_is_rejected():

    try:

        RecoveryContext(
            executable="calc.exe",

            window_title="Calculator",

            ui_adapter=Dummy(),

            replay_engine=None,

            graph=Dummy(),

            memory=Dummy(),
        )

        assert False

    except ValueError:

        pass


def test_missing_graph_is_rejected():

    try:

        RecoveryContext(
            executable="calc.exe",

            window_title="Calculator",

            ui_adapter=Dummy(),

            replay_engine=Dummy(),

            graph=None,

            memory=Dummy(),
        )

        assert False

    except ValueError:

        pass


def test_missing_memory_is_rejected():

    try:

        RecoveryContext(
            executable="calc.exe",

            window_title="Calculator",

            ui_adapter=Dummy(),

            replay_engine=Dummy(),

            graph=Dummy(),

            memory=None,
        )

        assert False

    except ValueError:

        pass


def main():

    print()

    print(
        "===== RECOVERY CONTEXT TESTS ====="
    )

    print()

    tests = [

        test_context_preserves_executable,

        test_context_preserves_window_title,

        test_context_preserves_runtime_objects,

        test_empty_executable_is_rejected,

        test_empty_window_title_is_rejected,

        test_missing_ui_adapter_is_rejected,

        test_missing_replay_engine_is_rejected,

        test_missing_graph_is_rejected,

        test_missing_memory_is_rejected,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All RecoveryContext tests passed successfully."
    )


if __name__ == "__main__":

    main()