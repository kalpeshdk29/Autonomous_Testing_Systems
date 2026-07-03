"""
File: explorer.py

Purpose:
    Base explorer interface.
"""

from abc import ABC
from abc import abstractmethod


class Explorer(ABC):
    """
    Base explorer.
    """

    @abstractmethod
    def explore(
        self,
        window,
        max_states: int = 100
    ):
        """
        Explore application.
        """
        pass