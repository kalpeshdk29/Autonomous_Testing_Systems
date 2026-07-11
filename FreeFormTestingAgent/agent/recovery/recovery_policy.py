from abc import ABC, abstractmethod

from agent.failure.failure_record import (
    FailureRecord,
)

from agent.recovery.recovery_result import (
    RecoveryResult,
)
from agent.recovery.recovery_context import RecoveryContext


class RecoveryPolicy(ABC):
    """
    Base class for every deterministic recovery policy.
    """

    @abstractmethod
    def recover(
        self,
        failure: FailureRecord,
        context: RecoveryContext,
    ) -> RecoveryResult:
        """
        Attempt recovery from one failure.

        Returns
        -------
        RecoveryResult
        """