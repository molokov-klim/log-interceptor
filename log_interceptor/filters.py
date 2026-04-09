"""Filter system for LogInterceptor.

Provides base interface and various filter implementations
for filtering log lines by different criteria.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from collections.abc import Callable


class BaseFilter(ABC):
    """Abstract base class for all filters.

    All filters must inherit from this class and implement
    the filter() method to define filtering logic.
    """

    @abstractmethod
    def filter(self, line: str) -> bool:
        """Check if line should be included.

        Args:
            line: Line to check.

        Returns:
            True if line should be included, False otherwise.

        """


class RegexFilter(BaseFilter):
    """Regular expression based filter.

    Filters lines by regular expression with support for
    whitelist (include matches) and blacklist (exclude matches) modes.

    Attributes:
        pattern: Compiled regular expression.
        mode: Filtering mode ('whitelist' or 'blacklist').

    """

    def __init__(
        self,
        pattern: str,
        *,
        mode: Literal["whitelist", "blacklist"] = "whitelist",
        case_sensitive: bool = True,
    ) -> None:
        """Initialize RegexFilter.

        Args:
            pattern: Regular expression for filtering.
            mode: Filtering mode:
                - 'whitelist': include only matching lines
                - 'blacklist': exclude matching lines
            case_sensitive: Consider case when matching.

        Raises:
            re.error: If pattern is invalid.

        """
        flags = 0 if case_sensitive else re.IGNORECASE
        self.pattern = re.compile(pattern, flags)
        self.mode = mode

    def filter(self, line: str) -> bool:
        """Check line against regular expression.

        Args:
            line: Line to check.

        Returns:
            True if line passes filter, False otherwise.

        """
        matches = bool(self.pattern.search(line))

        if self.mode == "whitelist":
            return matches
        return not matches  # blacklist


class PredicateFilter(BaseFilter):
    """Filter based on custom predicate function.

    Uses arbitrary function to determine if line should
    be included in result.

    Attributes:
        predicate: Predicate function for checking lines.

    """

    def __init__(self, predicate: Callable[[str], bool]) -> None:
        """Initialize PredicateFilter.

        Args:
            predicate: Function that takes string and returns bool.
                      True means line should be included.

        """
        self.predicate = predicate

    def filter(self, line: str) -> bool:
        """Check line using predicate.

        Args:
            line: Line to check.

        Returns:
            Result of applying predicate to line.

        """
        return self.predicate(line)


class CompositeFilter(BaseFilter):
    """Composite filter for combining multiple filters.

    Supports AND and OR logical operations for combining
    results of multiple filters.

    Attributes:
        filters: List of filters to combine.
        mode: Combination mode ('AND' or 'OR').

    """

    def __init__(
        self,
        filters: list[BaseFilter],
        *,
        mode: Literal["AND", "OR"] = "AND",
    ) -> None:
        """Initialize CompositeFilter.

        Args:
            filters: List of filters to combine.
            mode: Combination mode:
                - 'AND': line must pass all filters
                - 'OR': line must pass at least one filter

        """
        self.filters = filters
        self.mode = mode

    def filter(self, line: str) -> bool:
        """Apply all filters to line according to mode.

        Args:
            line: Line to check.

        Returns:
            Result of combined check of all filters.

        """
        if not self.filters:
            # Empty AND returns True (no conditions to check)
            # Empty OR returns False (no conditions satisfied)
            return self.mode == "AND"

        if self.mode == "AND":
            return all(f.filter(line) for f in self.filters)
        return any(f.filter(line) for f in self.filters)  # OR
