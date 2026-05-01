"""FetchResult dataclass — the unified return type for all data fetchers."""
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FetchResult:
    """Unified result container returned by every fetcher function.

    Attributes:
        source: Identifier for the data source (e.g. 'jira', 'weather', 'news', 'sports', 'mtg').
        status: Outcome of the fetch — 'success', 'failed', or 'skipped'.
        data: Parsed payload; structure is source-specific. None when status != 'success'.
        error_message: Human-readable description of the failure. None on success.
    """

    source: str
    status: str
    data: Any = None
    error_message: Optional[str] = None
