"""
Web crawler for FakeGuard.
Supports RSS feeds and basic web scraping.
"""
import logging
import hashlib
import re
from datetime import datetime, timezone
from typing import Optional
import requests
import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FakeGuard/1.0; +https://fakeguard.app/bot)"
}


def crawl_rss(url: str, limit: int = 20) -> list[dict]:
    """Parse RSS/Atom feed and return list of article dicts."""
    articles = []
    try:
        feed = feedparser.parse(url)
        if feed.bozo and not feed.entries:
            logger.warning(f"RSS parse error for {url}: {feed.bozo_exception}")
            return []

        for entry in feed.entries[:limit]:
            article = _rss_entry_to_dict(entry, url)
            if article:
                articles.append(article)

        logger.info(f"RSS crawled {len(articles)} articles from {url}")
    except Exception as e:
        logger.error(f"RSS crawl error for {url}: {e}")
    return articles


def _rss_entry_to_dict(entry, source_url: str) -> Optional[dict]:
    """Convert feedparser entry to article dict."""
    try:
        link = getattr(entry, "link", None)
        title = getattr(entry, "title", "").strip()
        if not link or not title:
            return None

        # Get content/summary
        content = ""
        if hasattr(entry, "content") and entry.content:
            content = BeautifulSoup(entry.content[0].value, "html.parser").get_text()
        elif hasattr(entry, "summary"):
            content = BeautifulSoup(entry.summary, "html.parser").get_text()
        content = clean_text(content)
        summary = content[:300] + "..." if len(content) > 300 else content

        # Published date
        published_at = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                pass

        # Image
        image_url = ""
        if hasattr(entry, "media_content") and entry.media_content:
            image_url = entry.media_content[0].get("url", "")
        elif hasattr(entry, "enclosures") and entry.enclosures:
            enc = entry.enclosures[0]
            if "image" in enc.get("type", ""):
                image_url = enc.get("href", "")

        # Detect language from title
        language = _detect_language(title + " " + content[:200])

        return {
            "url": link,
            "title": title,
            "content": content,
            "summary": summary,
            "author": getattr(entry, "author", ""),
            "image_url": image_url[:500] if image_url else "",
            "published_at": published_at,
            "language": language,
        }
    except Exception as e:
        logger.error(f"Entry parse error: {e}")
        return None


def scrape_url(url: str) -> Optional[dict]:
    """Scrape a single web page and extract article content."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "aside", "header", "form"]):
            tag.decompose()

        title = ""
        if soup.title:
            title = soup.title.string or ""
        if soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)

        # Try to find article content
        article_tag = (
            soup.find("article") or
            soup.find("div", class_=re.compile(r"article|content|post|entry", re.I)) or
            soup.find("main")
        )
        if article_tag:
            paragraphs = article_tag.find_all("p")
        else:
            paragraphs = soup.find_all("p")

        content = " ".join(p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30)
        content = clean_text(content)
        summary = content[:300] + "..." if len(content) > 300 else content

        # Try to get image
        image_url = ""
        og_image = soup.find("meta", property="og:image")
        if og_image:
            image_url = og_image.get("content", "")

        return {
            "url": url,
            "title": clean_text(title),
            "content": content,
            "summary": summary,
            "author": "",
            "image_url": image_url[:500],
            "published_at": None,
            "language": "ru",
        }
    except Exception as e:
        logger.error(f"Scrape error for {url}: {e}")
        return None


def _detect_language(text: str) -> str:
    """Simple heuristic language detection (ru/en)."""
    if not text:
        return "ru"
    # Count Cyrillic characters
    cyrillic = sum(1 for c in text if "\u0400" <= c <= "\u04ff")
    latin = sum(1 for c in text if "a" <= c.lower() <= "z")
    if cyrillic > latin:
        return "ru"
    if latin > cyrillic * 2:
        return "en"
    return "ru"


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()
