"""
Autonomous deterministic exploration continuation loop.

Architecture:

Coverage + Constraints
        ↓
Select Next Target
        ↓
Pre-Step Runtime Health Check
        ↓
Execute One Exploration Step
        ↓
Post-Step Runtime Health Check
        ↓
Detect Structured Execution Failure
        ↓
Graph + Memory Updated
        ↓
Checkpoint
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
        - check runtime health before execution
        - execute exactly one step
        - check runtime health after execution
        - collect step results
        - detect structured execution failures
        - store detected failures
        - checkpoint runtime knowledge
        - repeat until a stop condition is reached

    Non-responsibilities:
        - calculating coverage
        - ranking targets
        - selecting actions
        - replaying application state
        - executing UI actions
        - updating graph or memory
        - classifying detector-specific failure rules

    Those responsibilities remain delegated to already-tested
    components.
    """

    def __init__(
        self,
        target_selector,
        step_executor,
        limits: CoordinatorLimits | None = None,
        checkpoint_manager=None,
        failure_detector=None,
        failure_store=None,
        runtime_health_monitor=None,
        recovery_manager=None,
        recovery_context=None,
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

            checkpoint_manager:
                Optional persistence component exposing:

                    checkpoint()

                When supplied, checkpoints are created after
                attempted exploration work and detected runtime
                failures.

            failure_detector:
                Optional deterministic execution-failure detector
                exposing:

                    detect(step_result)

                The detector returns:

                    FailureRecord
                    or
                    None

            failure_store:
                Optional structured failure collection exposing:

                    add(failure)
                    failures

                Required when either:

                    - failure_detector is supplied
                    - runtime_health_monitor is supplied

            runtime_health_monitor:
                Optional runtime-health component exposing:

                    check(source_state_id)

                The monitor returns:

                    FailureRecord
                    or
                    None

        Backward Compatibility:
            Runtime-health monitoring, execution-failure detection,
            and persistence remain optional.

            Existing coordinator construction remains valid.
        """

        if failure_detector is not None and failure_store is None:

            raise ValueError(
                "failure_store is required " "when failure_detector is supplied."
            )

        if runtime_health_monitor is not None and failure_store is None:

            raise ValueError(
                "failure_store is required " "when runtime_health_monitor is supplied."
            )

        if (
            failure_store is not None
            and failure_detector is None
            and runtime_health_monitor is None
        ):

            raise ValueError(
                "failure_detector or "
                "runtime_health_monitor is required "
                "when failure_store is supplied."
            )

        if recovery_manager is not None and not hasattr(
            recovery_manager,
            "recover",
        ):
            raise ValueError("recovery_manager must implement recover().")
        
        if (
            recovery_context is not None
            and recovery_manager is None
        ):
            raise ValueError(
                "recovery_manager is required when "
                "recovery_context is supplied."
            )

        self.target_selector = target_selector

        self.step_executor = step_executor

        self.limits = limits or CoordinatorLimits()

        self.checkpoint_manager = checkpoint_manager

        self.failure_detector = failure_detector

        self.failure_store = failure_store

        self.runtime_health_monitor = runtime_health_monitor

        self._recovery_manager = recovery_manager
        
        self._recovery_context = recovery_context

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
            CoordinatorResult containing:

                - statistics
                - ordered step history
                - structured failure history
        """

        start_time = time.time()

        step_results = []

        run_failures = []

        successful_steps = 0

        failed_steps = 0

        new_states = 0

        stop_reason = None

        while True:

            # =================================================
            # STEP 1
            # CHECK CONTINUATION LIMITS
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
            # SELECT CURRENT EXPLORATION WORK
            # =================================================

            selected_target = self.target_selector.select_next_target()

            if selected_target is None:

                stop_reason = CoordinatorStopReason.NO_REMAINING_TARGETS

                break

            source_state_id = selected_target.state_id

            # =================================================
            # STEP 3
            # PRE-STEP RUNTIME HEALTH CHECK
            #
            # Do not attempt exploration work when the application
            # is already known to be unhealthy.
            # =================================================

            runtime_failure = self._check_runtime_health(
                source_state_id=source_state_id,
            )

            if runtime_failure is not None:

                continue_exploration, stop_reason = (
                    self._handle_runtime_failure(
                        runtime_failure,
                        run_failures,
                    )
                )

                if not continue_exploration:

                    break


            # =================================================
            # STEP 4
            # EXECUTE EXACTLY ONE EXPLORATION STEP
            # =================================================

            step_result = self.step_executor.execute_step(
                root_state_id=(root_state_id),
                source_state_id=(source_state_id),
            )

            step_results.append(step_result)

            # =================================================
            # STEP 5
            # UPDATE COORDINATOR STATISTICS
            # =================================================

            if step_result.execution_success:

                successful_steps += 1

                if step_result.new_state_discovered:

                    new_states += 1

            else:

                failed_steps += 1

            # =================================================
            # STEP 6
            # POST-STEP RUNTIME HEALTH CHECK
            #
            # Runtime failure takes priority over execution-failure
            # classification.
            #
            # Example:
            #
            #     action execution fails
            #             +
            #     application process disappeared
            #
            # The fundamental failure is:
            #
            #     APPLICATION_DISAPPEARED
            #
            # not merely:
            #
            #     ACTION_EXECUTION_FAILED
            # =================================================

            runtime_failure = self._check_runtime_health(
                source_state_id=source_state_id,
            )

            if runtime_failure is not None:

                continue_exploration, stop_reason = (
                    self._handle_runtime_failure(
                        runtime_failure,
                        run_failures,
                    )
                )

                if not continue_exploration:

                    break


            # =================================================
            # STEP 7
            # DETECT AND STORE STRUCTURED EXECUTION FAILURES
            #
            # This runs only when post-step runtime health is
            # healthy.
            #
            # The coordinator does not duplicate detector rules.
            # =================================================

            if self.failure_detector is not None:

                detected_failure = self.failure_detector.detect(step_result)

                if detected_failure is not None:

                    self._store_failure(
                        failure=(detected_failure),
                        run_failures=(run_failures),
                    )

            # =================================================
            # STEP 8
            # PERSIST UPDATED EXPLORATION KNOWLEDGE
            #
            # Checkpoint after every attempted step because both
            # successful and failed attempts may update memory.
            #
            # Persistence remains optional.
            # =================================================

            checkpoint_succeeded = self._try_checkpoint()

            if not checkpoint_succeeded:

                stop_reason = CoordinatorStopReason.CHECKPOINT_FAILED

                break

        duration = time.time() - start_time

        return CoordinatorResult(
            steps=len(step_results),
            successful_steps=(successful_steps),
            failed_steps=(failed_steps),
            new_states=(new_states),
            duration=duration,
            stop_reason=stop_reason,
            step_results=(step_results),
            failures=(run_failures),
        )

    def _check_runtime_health(
        self,
        source_state_id: str,
    ):
        """
        Execute one optional runtime-health check.

        Returns:
            FailureRecord:
                Runtime failure detected.

            None:
                Monitoring is disabled or runtime is healthy.
        """

        if self.runtime_health_monitor is None:

            return None

        return self.runtime_health_monitor.check(source_state_id=(source_state_id))

    def _store_failure(
        self,
        failure,
        run_failures: list,
    ) -> None:
        """
        Store one detected failure in both:

            - persistent/live FailureStore
            - current CoordinatorResult history
        """

        self.failure_store.add(failure)

        run_failures.append(failure)

    def _try_checkpoint(
        self,
    ) -> bool:
        """
        Attempt one optional checkpoint.

        Returns:
            True:
                Persistence is disabled or checkpoint succeeded.

            False:
                Checkpoint failed.
        """

        if self.checkpoint_manager is None:

            return True

        try:

            self.checkpoint_manager.checkpoint()

            return True

        except Exception:

            return False

    def _attempt_runtime_recovery(
    self,
    failure,
    )-> bool:
        """
        Attempt runtime recovery.

        Returns
        -------
        bool
            True if exploration may continue.
        """
        if self._recovery_manager is None:
            
            return (
                    False,
                    CoordinatorStopReason.RUNTIME_HEALTH_FAILED,
                )

        result = self._recovery_manager.recover(
            failure,
            self._recovery_context,
        )

        return result.success

    def _handle_runtime_failure(
        self,
        failure,
        run_failures,
    ):
        """
        Handle one runtime failure.

        Returns
        -------
        tuple[bool, CoordinatorStopReason | None]

        continue_exploration:
            True if exploration may continue.

        stop_reason:
            Stop reason when continuation is impossible.
        """

        self._store_failure(
            failure=failure,
            run_failures=run_failures,
        )

        if self._recovery_manager is not None:

            recovery = self._recovery_manager.recover(
                failure,
                self._recovery_context,
            )

            if recovery.success:

                return (
                    True,
                    None,
                )

        checkpoint_succeeded = self._try_checkpoint()

        if not checkpoint_succeeded:

            return (
                False,
                CoordinatorStopReason.CHECKPOINT_FAILED,
            )

        return (
            False,
            CoordinatorStopReason.RECOVERY_FAILED,
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

        if self.limits.max_steps is not None and steps >= self.limits.max_steps:

            return CoordinatorStopReason.MAX_STEPS_REACHED

        elapsed_time = time.time() - start_time

        if (
            self.limits.max_duration is not None
            and elapsed_time >= self.limits.max_duration
        ):

            return CoordinatorStopReason.MAX_DURATION_REACHED

        if (
            self.limits.max_failures is not None
            and failures >= self.limits.max_failures
        ):

            return CoordinatorStopReason.MAX_FAILURES_REACHED

        return None
