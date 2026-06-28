import subprocess
import sys

print()
print("PYTHON:")
print(sys.executable)
print()

TESTS = [

    "tests.unit.memory.test_exploration_memory",

    "tests.integration.ui.test_uia",

    "tests.integration.ui.test_calculator",

    "tests.integration.ui.test_state_values",

    "tests.integration.actions.test_action_discovery",

    "tests.integration.actions.test_action_execution",

    "tests.integration.state.test_state_transition",

    "tests.integration.graph.test_state_graph",
]


def main():

    passed = 0

    for test in TESTS:

        print()
        print("=" * 70)

        print(
            "RUNNING:",
            test
        )

        print("=" * 70)

        result = subprocess.run(
    [
        sys.executable,
        "-m",
        test
    ]
)

        if result.returncode == 0:

            passed += 1

    print()
    print("=" * 70)

    print(
        f"PASSED: "
        f"{passed}/{len(TESTS)}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()