"""Sports fetcher — retrieves the most recent LA Dodgers MLB game result."""
import logging
from datetime import datetime, timezone

from scripts.utils.fetch_result import FetchResult
from scripts.utils.http_client import get

logger = logging.getLogger(__name__)

_API_URL = "https://statsapi.mlb.com/api/v1/schedule"
_DODGERS_TEAM_ID = 119  # LA Dodgers official MLB team ID


def _extract_game_data(game: dict) -> dict:
    """Parse a game dict from the MLB API schedule endpoint."""
    teams = game.get("teams", {})
    home = teams.get("home", {})
    away = teams.get("away", {})

    home_team = home.get("team", {})
    away_team = away.get("team", {})

    home_id = home_team.get("id")
    away_id = away_team.get("id")

    if home_id == _DODGERS_TEAM_ID:
        dodgers_score = home.get("score", 0)
        opponent_score = away.get("score", 0)
        opponent = away_team.get("name", "Unknown")
    else:
        dodgers_score = away.get("score", 0)
        opponent_score = home.get("score", 0)
        opponent = home_team.get("name", "Unknown")

    # Determine series status from linescore if available
    linescore = game.get("linescore", {})
    series_status = linescore.get("note", "")
    if not series_status:
        series_desc = game.get("seriesDescription", "")
        game_number = game.get("gameNumber", "")
        series_status = f"{series_desc} Game {game_number}" if series_desc else "Regular Season"

    return {
        "opponent": opponent,
        "dodgers_score": int(dodgers_score),
        "opponent_score": int(opponent_score),
        "series_status": series_status,
    }


def fetch(config: dict) -> FetchResult:
    """Fetch the most recent completed Dodgers game from the MLB Stats API.

    Args:
        config: Unused (MLB Stats API requires no authentication).

    Returns:
        FetchResult with status='success' and data containing game details,
        or data={'message': 'No recent Dodgers game available.'} if off-season.
        FetchResult with status='failed' on any error.
    """
    try:
        current_year = datetime.now(tz=timezone.utc).year
        params = {
            "teamId": _DODGERS_TEAM_ID,
            "sportId": 1,
            "gameType": "R",
            "hydrate": "linescore",
            "season": current_year,
        }

        response = get(_API_URL, params=params)

        dates = response.get("dates", [])
        # Iterate dates in reverse (most recent first)
        for date_entry in reversed(dates):
            games = date_entry.get("games", [])
            for game in games:
                status = game.get("status", {})
                status_code = status.get("abstractGameState", "")
                if status_code == "Final":
                    game_data = _extract_game_data(game)
                    logger.info(
                        "Sports: Dodgers vs %s — %d:%d",
                        game_data["opponent"],
                        game_data["dodgers_score"],
                        game_data["opponent_score"],
                    )
                    return FetchResult(source="sports", status="success", data=game_data)

        # EC-005: No completed game found
        logger.info("Sports: No recent completed Dodgers game found")
        return FetchResult(
            source="sports",
            status="success",
            data={"message": "No recent Dodgers game available."},
        )

    except Exception as exc:
        logger.warning("Sports fetch failed: %s", exc)
        return FetchResult(source="sports", status="failed", error_message=str(exc))
