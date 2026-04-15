"""JST（科学技術振興機構）公募情報の収集

RSSフィード: https://www.jst.go.jp/rss/bosyu.xml
"""

from __future__ import annotations

import feedparser

from ..models import CollectionResult, PolicyItem

RSS_URL = "https://www.jst.go.jp/rss/bosyu.xml"
SOURCE = "jst"
SOURCE_NAME = "科学技術振興機構（JST）"


def collect_jst() -> CollectionResult:
    """JST公募情報をRSSフィードから収集する"""
    result = CollectionResult(source=SOURCE, source_name=SOURCE_NAME)

    try:
        feed = feedparser.parse(RSS_URL)

        if feed.bozo and not feed.entries:
            result.errors.append(f"RSS解析エラー: {feed.bozo_exception}")
            return result

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if not title or not link:
                continue

            # 日付の解析
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    from time import strftime, mktime

                    published = strftime(
                        "%Y-%m-%d", entry.published_parsed
                    )
                except (ValueError, OverflowError):
                    pass

            # descriptionの取得
            description = entry.get("summary", "").strip() or None

            item = PolicyItem(
                title=title,
                url=link,
                source=SOURCE,
                source_name=SOURCE_NAME,
                published_date=published,
                category="公募",
                description=description,
            )
            result.items.append(item)

    except Exception as e:
        result.errors.append(f"JST収集エラー: {e}")

    return result
