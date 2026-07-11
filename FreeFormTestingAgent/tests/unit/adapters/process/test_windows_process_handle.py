"""
File:
    test_windows_process_handle.py

Purpose:
    Verify exact-PID Windows process tracking.

Scope:
    subprocess is replaced with a deterministic fake.

    Real Windows behavior belongs to the Calculator integration
    test.
"""

from unittest.mock import patch

from adapters.process.windows_process_handle import (
    WindowsProcessHandle,
)


class FakeCompletedProcess:

    def __init__(
        self,
        returncode: int,
        stdout: str,
    ):

        self.returncode = returncode

        self.stdout = stdout


def test_running_exact_pid_returns_none():

    handle = WindowsProcessHandle(
        process_id=32408
    )

    result = FakeCompletedProcess(
        returncode=0,

        stdout=(
            '"CalculatorApp.exe",'
            '"32408",'
            '"Console",'
            '"1",'
            '"10,000 K"'
        ),
    )

    with patch(
        "adapters.process."
        "windows_process_handle."
        "subprocess.run",

        return_value=result,
    ):

        assert handle.poll() is None


def test_missing_pid_returns_disappeared_code():

    handle = WindowsProcessHandle(
        process_id=32408
    )

    result = FakeCompletedProcess(
        returncode=0,

        stdout=(
            "INFO: No tasks are running "
            "which match the specified criteria."
        ),
    )

    with patch(
        "adapters.process."
        "windows_process_handle."
        "subprocess.run",

        return_value=result,
    ):

        assert (
            handle.poll()
            ==
            WindowsProcessHandle
            .DISAPPEARED_RETURN_CODE
        )


def test_empty_tasklist_output_returns_disappeared_code():

    handle = WindowsProcessHandle(
        process_id=32408
    )

    result = FakeCompletedProcess(
        returncode=0,

        stdout="",
    )

    with patch(
        "adapters.process."
        "windows_process_handle."
        "subprocess.run",

        return_value=result,
    ):

        assert handle.poll() is not None


def test_tasklist_failure_returns_disappeared_code():

    handle = WindowsProcessHandle(
        process_id=32408
    )

    result = FakeCompletedProcess(
        returncode=1,

        stdout="",
    )

    with patch(
        "adapters.process."
        "windows_process_handle."
        "subprocess.run",

        return_value=result,
    ):

        assert handle.poll() is not None


def test_different_pid_is_not_treated_as_tracked_process():

    handle = WindowsProcessHandle(
        process_id=32408
    )

    result = FakeCompletedProcess(
        returncode=0,

        stdout=(
            '"CalculatorApp.exe",'
            '"99999",'
            '"Console",'
            '"1",'
            '"10,000 K"'
        ),
    )

    with patch(
        "adapters.process."
        "windows_process_handle."
        "subprocess.run",

        return_value=result,
    ):

        assert handle.poll() is not None


def test_process_id_is_exposed_as_pid():

    handle = WindowsProcessHandle(
        process_id=32408
    )

    assert handle.pid == 32408


def test_zero_process_id_is_rejected():

    try:

        WindowsProcessHandle(
            process_id=0
        )

        assert False, (
            "Expected invalid PID to be rejected."
        )

    except ValueError as error:

        assert (
            "process_id"
            in str(error)
        )


def test_negative_process_id_is_rejected():

    try:

        WindowsProcessHandle(
            process_id=-1
        )

        assert False, (
            "Expected invalid PID to be rejected."
        )

    except ValueError as error:

        assert (
            "process_id"
            in str(error)
        )


def test_non_integer_process_id_is_rejected():

    try:

        WindowsProcessHandle(
            process_id="32408"
        )

        assert False, (
            "Expected non-integer PID to be rejected."
        )

    except ValueError as error:

        assert (
            "process_id"
            in str(error)
        )


def main():

    print()

    print(
        "===== WINDOWS PROCESS HANDLE TESTS ====="
    )

    print()

    tests = [
        test_running_exact_pid_returns_none,

        test_missing_pid_returns_disappeared_code,

        test_empty_tasklist_output_returns_disappeared_code,

        test_tasklist_failure_returns_disappeared_code,

        test_different_pid_is_not_treated_as_tracked_process,

        test_process_id_is_exposed_as_pid,

        test_zero_process_id_is_rejected,

        test_negative_process_id_is_rejected,

        test_non_integer_process_id_is_rejected,
    ]

    for test in tests:

        test()

        print(
            f"PASS: {test.__name__}"
        )

    print()

    print(
        "All WindowsProcessHandle tests "
        "passed successfully."
    )


if __name__ == "__main__":

    main()