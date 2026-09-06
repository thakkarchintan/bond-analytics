"""News routes — NewsAPI articles + optional LLM summary."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta

import requests
from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/news", tags=["news"])

NEWS_API_KEY      = os.getenv("NEWS_API_KEY", "")
COHERE_API_KEY    = os.getenv("COHERE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")


def _fetch_articles(query: str, page_size: int = 10) -> list[dict]:
    if not NEWS_API_KEY:
        return []
    try:
        from_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
                "from": from_date,
                "apiKey": NEWS_API_KEY,
            },
            timeout=10,
        )
        data = resp.json()
        articles = data.get("articles", [])
        return [
            {
                "title":       a.get("title", ""),
                "description": a.get("description", ""),
                "url":         a.get("url", ""),
                "source":      a.get("source", {}).get("name", ""),
                "publishedAt": a.get("publishedAt", ""),
                "urlToImage":  a.get("urlToImage", ""),
            }
            for a in articles
            if a.get("title") and "[Removed]" not in (a.get("title") or "")
        ]
    except Exception:
        return []


def _summarise_cohere(texts: list[str]) -> str:
    if not COHERE_API_KEY or not texts:
        return ""
    try:
        combined = "\n\n".join(texts[:8])[:4000]
        resp = requests.post(
            "https://api.cohere.ai/v1/summarize",
            headers={"Authorization": f"Bearer {COHERE_API_KEY}", "Content-Type": "application/json"},
            json={"text": combined, "length": "medium", "format": "paragraph", "model": "command"},
            timeout=20,
        )
        return resp.json().get("summary", "")
    except Exception:
        return ""


def _summarise_openrouter(texts: list[str], query: str) -> str:
    if not OPENROUTER_API_KEY or not texts:
        return ""
    try:
        combined = "\n\n".join(texts[:8])[:5000]
        prompt = (
            f"You are a fixed income analyst. Summarise the following news articles about '{query}' "
            f"in 3-4 concise bullet points, focusing on market impact and key data points.\n\n{combined}"
        )
        resp = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://bond-analytics.onrender.com",
            },
            json={
                "model": "mistralai/mistral-7b-instruct",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 400,
            },
            timeout=30,
        )
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return ""


@router.get("")
def get_news(q: str = Query("bonds interest rates", description="Search query")) -> dict:
    articles = _fetch_articles(q, page_size=15)

    summary = ""
    if articles:
        texts = [f"{a['title']}. {a['description'] or ''}" for a in articles]
        # Try OpenRouter first, then Cohere
        if OPENROUTER_API_KEY:
            summary = _summarise_openrouter(texts, q)
        if not summary and COHERE_API_KEY:
            summary = _summarise_cohere(texts)

    has_news_key = bool(NEWS_API_KEY)
    has_llm_key  = bool(COHERE_API_KEY or OPENROUTER_API_KEY)

    return {
        "query":        q,
        "articles":     articles,
        "summary":      summary,
        "has_news_key": has_news_key,
        "has_llm_key":  has_llm_key,
        "article_count": len(articles),
    }
