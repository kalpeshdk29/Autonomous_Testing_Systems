"""
File: action_filter.py

Purpose:
    Defines the interface for filtering actions
    during exploration.

Architecture:

Discovered Actions
        ↓
ActionFilter
        ↓
Allowed Actions
"""

from abc import ABC
from abc import abstractmethod


class ActionFilter(ABC):
    """
    Base action filter.

    Determines whether an action
    should be explored.
    """

    @abstractmethod
    def allow(
        self,
        action
    ) -> bool:
        """
        Check whether action is allowed.

        Parameters
        ----------
        action:
            Action to evaluate.

        Returns
        -------
        bool
        """
        pass