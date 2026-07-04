"""
File: explorer.py

Purpose:
    Defines the common interface for all
    application exploration strategies.
"""

from abc import ABC
from abc import abstractmethod


class Explorer(ABC):
    """
    Base interface for application explorers.
    """

    @abstractmethod
    def explore(
        self,
        window
    ):
        """
        Explore the connected application.

        Parameters
        ----------
        window:
            Initial connected application window.
        """
        pass