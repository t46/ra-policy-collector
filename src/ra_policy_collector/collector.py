"""メインの収集オーケストレーター"""

from __future__ import annotations

import sys
from pathlib import Path

from .models import (
    CollectionResult,
    PolicyItem,
    detect_new_items,
    load_previous_items,
    save_items,
)
from .report import generate_latest_symlink, generate_report
from .sources import collect_jst, collect_jsps, collect_mext

# プロジェクトルートからの相対パス
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 収集関数のレジストリ
COLLECTORS: list[callable] = [
    collect_mext,
    collect_jst,
    collect_jsps,
]


def run_collection() -> tuple[list[CollectionResult], dict[str, list[PolicyItem]]]:
    """全ソースから情報を収集する"""
    results: list[CollectionResult] = []
    new_items: dict[str, list[PolicyItem]] = {}

    for collector in COLLECTORS:
        print(f"収集中: {collector.__module__.split('.')[-1]}...")
        result = collector()
        results.append(result)

        if result.success:
            print(f"  -> {result.count}件取得")
        else:
            print(f"  -> エラー: {', '.join(result.errors)}")

        # 前回データとの差分検出
        previous = load_previous_items(DATA_DIR, result.source)
        new = detect_new_items(result.items, previous)
        new_items[result.source] = new

        if new:
            print(f"  -> 新規: {len(new)}件")

        # データ保存
        if result.items:
            save_items(DATA_DIR, result.source, result.items)

    return results, new_items


def main() -> None:
    """メインエントリーポイント"""
    print("=" * 60)
    print("科学技術政策情報 自動収集システム")
    print("=" * 60)
    print()

    results, new_items = run_collection()

    print()
    print("レポート生成中...")
    report_path = generate_report(results, new_items, OUTPUT_DIR)
    generate_latest_symlink(OUTPUT_DIR, report_path)
    print(f"レポート: {report_path}")

    # サマリー表示
    total = sum(r.count for r in results)
    total_new = sum(len(items) for items in new_items.values())
    errors = sum(1 for r in results if not r.success)

    print()
    print(f"完了: {total}件収集, {total_new}件新規, {errors}件エラー")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
