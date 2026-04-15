"""文部科学省 公募情報の収集

対象ページ: https://www.mext.go.jp/b_menu/boshu/index.htm
科学技術・学術政策局関連の公募情報をスクレイピングで取得する。
"""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from ..models import CollectionResult, PolicyItem

BASE_URL = "https://www.mext.go.jp"
INDEX_URL = f"{BASE_URL}/b_menu/boshu/index.htm"
SOURCE = "mext"
SOURCE_NAME = "文部科学省"

# 和暦→西暦変換
ERA_MAP = {
    "令和": 2018,  # 令和元年 = 2019, 令和N年 = 2018 + N
    "平成": 1988,
}


def _parse_japanese_date(text: str) -> str | None:
    """和暦日付文字列をYYYY-MM-DDに変換する"""
    # 令和8年4月13日 のようなパターン
    m = re.search(r"(令和|平成)(\d+)年(\d+)月(\d+)日", text)
    if m:
        era, year, month, day = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        western_year = ERA_MAP.get(era, 0) + year
        return f"{western_year:04d}-{month:02d}-{day:02d}"
    return None


def collect_mext() -> CollectionResult:
    """文部科学省の公募情報をスクレイピングで収集する"""
    result = CollectionResult(source=SOURCE, source_name=SOURCE_NAME)

    try:
        resp = httpx.get(INDEX_URL, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        resp.encoding = resp.charset_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "lxml")

        # 公募情報のリンクを含むリスト要素を探す
        # MEXT のページは <li> の中に日付テキストと <a> タグがある構造
        links_found = set()

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            title = a_tag.get_text(strip=True)

            # 公募詳細ページへのリンクをフィルタ
            if not title or len(title) < 5:
                continue
            if "/b_menu/boshu/" not in href and "/a_menu/" not in href:
                continue
            # index自身は除外
            if href.endswith("index.htm") or href.endswith("index.html"):
                continue

            # 絶対URLに変換
            if href.startswith("/"):
                url = BASE_URL + href
            elif href.startswith("http"):
                url = href
            else:
                continue

            if url in links_found:
                continue
            links_found.add(url)

            # 親要素から日付を抽出
            parent = a_tag.parent
            parent_text = parent.get_text() if parent else ""
            published = _parse_japanese_date(parent_text)

            # カテゴリの推定
            category = "公募"
            if "結果" in title or "採択" in title:
                category = "公募結果"
            elif "報道" in parent_text:
                category = "報道発表"

            item = PolicyItem(
                title=title,
                url=url,
                source=SOURCE,
                source_name=SOURCE_NAME,
                published_date=published,
                category=category,
            )
            result.items.append(item)

    except httpx.HTTPError as e:
        result.errors.append(f"MEXT HTTP エラー: {e}")
    except Exception as e:
        result.errors.append(f"MEXT 収集エラー: {e}")

    return result
