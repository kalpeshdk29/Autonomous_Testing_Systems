"""
Autonomous deterministic exploration continuation loop.

Architecture:

Coverage + Constraints
        ↓
Select Next Target
        ↓
Execute One Exploration Step
        ↓
Graph + Memory Updated
        ↓
Repeat
"""

import time

from agent.coordinator.coordinator_limits import (
    CoordinatorLimits,
)

from agent.coordinator.coordinator_result import (
    CoordinatorResult,
)

from agent.coordinator.coordinator_stop_reason import (
    CoordinatorStopReason,
)


class ExplorationCoordinator:
    """
    Repeatedly execute deterministic continuation steps.

    Responsibility:
        - enforce continuation-run limits
        - request the next exploration target
        - execute exactly one step
        - collect step results
        - repeat until a stop condition is reached

    Non-responsibilities:
        - calculating coverage
        - ranking targets
        - selecting actions
        - replaying application state
        - executing UI actions
        - updating graph or memory

    Those responsibilities remain delegated to the already-tested
    components.
    """

    def __init__(
        self,
        target_selector,
        step_executor,
        limits: CoordinatorLimits | None = None,
    ) -> None:
        """
        Initialize the coordinator.

        Args:
            target_selector:
                Existing ExplorationTargetSelector.

            step_executor:
                Existing ExplorationStepExecutor.

            limits:
                Continuation-phase budget.
        """

        self.target_selector = target_selector

        self.step_executor = step_executor

        self.limits = limits or CoordinatorLimits()

    def run(
        self,
        root_state_id: str,
    ) -> CoordinatorResult:
        """
        Continue exploration autonomously until a stop condition
        is reached.

        Args:
            root_state_id:
                Root state of the current exploration session.

                Every single step may need it for replay.

        Returns:
            CoordinatorResult containing statistics and ordered
            step history.
        """

        start_time = time.time()

        step_results = []

        successful_steps = 0

        failed_steps = 0

        new_states = 0

        stop_reason = None

        while True:

            # =================================================
            # STEP 1
            # Check continuation-run limits before selecting
            # more work.
            # =================================================

            stop_reason = self._get_limit_stop_reason(
                steps=len(step_results),
                failures=failed_steps,
                start_time=start_time,
            )

            if stop_reason is not None:
                break

            # =================================================
            # STEP 2
            # Ask the target-selection layer for current work.
            #
            # The selector reads current CoverageEngine state,
            # so graph and memory updates from the previous step
            # are naturally reflected here.
            # =================================================

            selected_target = (
                self.target_selector.select_next_target()
            )

            if selected_target is None:

                stop_reason = (
                    CoordinatorStopReason
                    .NO_REMAINING_TARGETS
                )

                break

            # =================================================
            # STEP 3
            # Execute exactly one already-tested exploration step.
            # =================================================

            step_result = (
                self.step_executor.execute_step(
                    root_state_id=root_state_id,
                    source_state_id=(
                        selected_target.state_id
                    ),
                )
            )

            step_results.append(
                step_result
            )

            # =================================================
            # STEP 4
            # Update coordinator statistics.
            # =================================================

            if step_result.execution_success:

                successful_steps += 1

                if step_result.new_state_discovered:

                    new_states += 1

            else:

                failed_steps += 1

        duration = time.time() - start_time

        return CoordinatorResult(
            steps=len(step_results),
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            new_states=new_states,
            duration=duration,
            stop_reason=stop_reason,
            step_results=step_results,
        )

    def _get_limit_stop_reason(
        self,
        steps: int,
        failures: int,
        start_time: float,
    ):
        """
        Return the first reached coordinator limit.

        Limit precedence:

            1. max_steps
            2. max_duration
            3. max_failures

        This mirrors the deterministic style already used by the
        existing BFS exploration limit checks.
        """

        if (
            self.limits.max_steps is not None
            and
            steps >= self.limits.max_steps
        ):

            return (
                CoordinatorStopReason
                .MAX_STEPS_REACHED
            )

        elapsed_time = (
            time.time() - start_time
        )

        if (
            self.limits.max_duration is not None
            and
            elapsed_time >= self.limits.max_duration
        ):

            return (
                CoordinatorStopReason
                .MAX_DURATION_REACHED
            )

        if (
            self.limits.max_failures is not None
            and
            failures >= self.limits.max_failures
        ):

            return (
                CoordinatorStopReason
                .MAX_FAILURES_REACHED
            )

        return None