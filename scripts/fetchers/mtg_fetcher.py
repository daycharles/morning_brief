"""MTG fetcher — retrieves Magic: The Gathering sets released in the last 7 days via Scryfall API."""
import logging
from datetime import datetime, timedelta, timezone

from scripts.utils.fetch_result import FetchResult
from scripts.utils.http_client import get

logger = logging.getLogger(__name__)

_API_URL = "https://api.scryfall.com/sets"
_LOOKBACK_DAYS = 7


def _format_description(mtg_set: dict) -> str:
    """Build a human-readable description for an MTG set."""
    card_count = mtg_set.get("card_count")
    set_type = mtg_set.get("set_type", "")
    if card_count is not None:
        return f"{card_count} cards"
    return set_type.replace("_", " ").title() if set_type else "MTG Set"


def fetch(config: dict) -> FetchResult:
    """Fetch MTG sets released within the last 7 days from Scryfall.

    Args:
        config: Unused (Scryfall API requires no authentication).

    Returns:
        FetchResult with status='success' and data={'sets': [...]} on success.
        FetchResult with status='failed' on any error.
    """
    try:
        response = get(_API_URL)

        all_sets = response.get("data", [])
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=_LOOKBACK_DAYS)
        cutoff_date = cutoff.date()

        recent_sets = []
        for mtg_set in all_sets:
            released_at = mtg_set.get("released_at", "")
            if not released_at:
                continue
            try:
                release_date = datetime.strptime(released_at, "%Y-%m-%d").date()
            except ValueError:
                continue
            if release_date >= cutoff_date:
                recent_sets.append({
                    "set_name": mtg_set.get("name", "Unknown Set"),
                    "release_date": released_at,
                    "description": _format_description(mtg_set),
                })

        logger.info(
            "MTG: found %d sets released in the last %d days",
            len(recent_sets),
            _LOOKBACK_DAYS,
        )

        data = {"sets": recent_sets}
        if not recent_sets:
            data["message"] = "No new MTG releases in the last 7 days."

        return FetchResult(source="mtg", status="success", data=data)

    except Exception as exc:
        logger.warning("MTG fetch failed: %s", exc)
        return FetchResult(source="mtg", status="failed", error_message=str(exc))
