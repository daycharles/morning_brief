"""News fetcher — retrieves top 5 US political headlines from NewsAPI."""
import logging

from scripts.utils.fetch_result import FetchResult
from scripts.utils.http_client import get

logger = logging.getLogger(__name__)

_API_URL = "https://newsapi.org/v2/top-headlines"


def fetch(config: dict) -> FetchResult:
    """Fetch top 5 US political headlines from NewsAPI.

    Args:
        config: Dict with key:
            - newsapi_key: NewsAPI authentication key (required)

    Returns:
        FetchResult with status='success' and data={'articles': [...]} on success.
        FetchResult with status='failed' on any error.
    """
    try:
        newsapi_key = config.get("newsapi_key", "")
        if not newsapi_key:
            raise ValueError("Missing required config key: newsapi_key")

        headers = {"X-Api-Key": newsapi_key}
        params = {
            "country": "us",
            "category": "politics",
            "pageSize": 5,
        }

        response = get(_API_URL, headers=headers, params=params)

        raw_articles = response.get("articles", [])

        articles = []
        for article in raw_articles:
            source_obj = article.get("source", {})
            published_at = article.get("publishedAt", "")
            articles.append({
                "title": article.get("title", ""),
                "source": source_obj.get("name", "Unknown"),
                "published_date": published_at[:10] if published_at else "",
                "url": article.get("url", ""),
            })

        logger.info("News: fetched %d headlines", len(articles))

        data = {"articles": articles}
        if not articles:
            data["message"] = "No headlines available."

        return FetchResult(source="news", status="success", data=data)

    except Exception as exc:
        logger.warning("News fetch failed: %s", exc)
        return FetchResult(source="news", status="failed", error_message=str(exc))
