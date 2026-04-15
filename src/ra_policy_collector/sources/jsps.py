"""JSPS（日本学術振興会）科研費公募情報の収集

対象ページ:
- https://www.jsps.go.jp/j-grantsinaid/02_koubo/ （科研費公募）
- https://www.jsps.go.jp/j-grantsinaid/index.html （科研費トップ）
"""

from __future__ import annotations

import re

import httpx
from bs4 import BeautifulSoup

from ..models import CollectionResult, PolicyItem

BASE_URL = "https://www.jsps.go.jp"
PAGES = [
    f"{BASE_URL}/j-grantsinaid/index.html",
    f"{BASE_URL}/j-grantsinaid/02_koubo/",
]
SOURCE = "jsps"
SOURCE_NAME = "日本学術振興会（JSPS）"

ERA_MAP = {
    "令和": 2018,
    "平成": 1988,
}


def _parse_japanese_date(text: str) -> str | None:
    """和暦日付文字列をYYYY-MM-DDに変換する"""
    m = re.search(r"(令和|平成)(\d+)年(\d+)月(\d+)日", text)
    if m:
        era, year, month, day = (
            m.group(1),
            int(m.group(2)),
            int(m.group(3)),
            int(m.group(4)),
        )
        western_year = ERA_MAP.get(era, 0) + year
        return f"{western_year:04d}-{month:02d}-{day:02d}"
    # YYYY.MM.DD or YYYY/MM/DD
    m = re.search(r"(\d{4})[./](\d{1,2})[./](\d{1,2})", text)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None


def _normalize_url(href: str, page_url: str) -> str | None:
    """相対URLを絶対URLに変換"""
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE_URL + href
    if href.startswith("../"):
        # ページURLの親ディレクトリを基準に解決
        from urllib.parse import urljoin

        return urljoin(page_url, href)
    if href.startswith("./") or not href.startswith("#"):
        from urllib.parse import urljoin

        return urljoin(page_url, href)
    return None


def collect_jsps() -> CollectionResult:
    """JSPS科研費関連の公募情報をスクレイピングで収集する"""
    result = CollectionResult(source=SOURCE, source_name=SOURCE_NAME)
    seen_urls = set()

    for page_url in PAGES:
        try:
            resp = httpx.get(page_url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
            resp.encoding = resp.charset_encoding or "utf-8"
            soup = BeautifulSoup(resp.text, "lxml")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                title = a_tag.get_text(strip=True)

                if not title or len(title) < 5:
                    continue

                # 外部リンク（他機関）は除外
                url = _normalize_url(href, page_url)
                if not url:
                    continue
                if not url.startswith(BASE_URL) and "jsps.go.jp" not in url:
                    continue
                if url in seen_urls:
                    continue

                # 公募・応募に関連するリンクをフィルタ
                keywords = ["公募", "募集", "応募", "申請", "koubo", "boshu", "call"]
                parent_text = a_tag.parent.get_text() if a_tag.parent else ""
                combined = (title + href + parent_text).lower()

                if not any(kw in combined for kw in keywords):
                    # 科研費に関連するキーワードも許可
                    kakenhi_kw = ["科研費", "研究種目", "kaken", "grantsinaid"]
                    if not any(kw in combined for kw in kakenhi_kw):
                        continue

                seen_urls.add(url)

                published = _parse_japanese_date(parent_text)

                item = PolicyItem(
                    title=title,
                    url=url,
                    source=SOURCE,
                    source_name=SOURCE_NAME,
                    published_date=published,
                    category="公募",
                    description=None,
                )
                result.items.append(item)

        except httpx.HTTPError as e:
            result.errors.append(f"JSPS HTTP エラー ({page_url}): {e}")
        except Exception as e:
            result.errors.append(f"JSPS 収集エラー ({page_url}): {e}")

    return result
