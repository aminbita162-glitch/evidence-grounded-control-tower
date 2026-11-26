"""Pagination and size limits (Part 3 §3.17, P10-T01).

Typed pagination parameters with configurable size limits.  Every list
endpoint enforces the default and maximum page size to prevent excessive
result sets.
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "PageParams",
    "PageResult",
    "paginate",
]

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class PageParams:
    """Validated pagination parameters."""

    page: int = 1
    page_size: int = DEFAULT_PAGE_SIZE

    def __post_init__(self) -> None:
        """Validate page and page_size."""
        if self.page < 1:
            raise ValueError(f"page must be >= 1, got {self.page}")
        if self.page_size < 1:
            raise ValueError(f"page_size must be >= 1, got {self.page_size}")
        if self.page_size > MAX_PAGE_SIZE:
            raise ValueError(f"page_size must be <= {MAX_PAGE_SIZE}, got {self.page_size}")

    @property
    def offset(self) -> int:
        """Return the zero-based offset for this page."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Return the SQL LIMIT value."""
        return self.page_size


@dataclass(frozen=True)
class PageResult:
    """A paginated result envelope."""

    items: list[dict[str, object]]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        """Total number of pages."""
        if self.total == 0:
            return 1
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Whether a next page exists."""
        return self.page < self.total_pages


def paginate(
    items: list[dict[str, object]],
    params: PageParams,
    total: int | None = None,
) -> PageResult:
    """Slice *items* according to *params*.

    Args:
        items: The full ordered list (already loaded).
        params: Validated page parameters.
        total: Override the total count (defaults to ``len(items)``).
    """

    if total is None:
        total = len(items)
    start = params.offset
    end = start + params.limit
    return PageResult(
        items=items[start:end],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )
