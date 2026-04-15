"""Markdown レポート生成"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import CollectionResult, PolicyItem


def generate_report(
    results: list[CollectionResult],
    new_items: dict[str, list[PolicyItem]],
    output_dir: Path,
) -> Path:
    """収集結果をMarkdownレポートとして生成する"""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    report_path = output_dir / f"{today}-report.md"

    lines: list[str] = []
    lines.append(f"# 科学技術政策情報レポート ({today})\n")
    lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # サマリー
    total_items = sum(r.count for r in results)
    total_new = sum(len(items) for items in new_items.values())
    error_sources = [r.source_name for r in results if not r.success]

    lines.append("## サマリー\n")
    lines.append(f"| 指標 | 値 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 収集ソース数 | {len(results)} |")
    lines.append(f"| 総アイテム数 | {total_items} |")
    lines.append(f"| 新規アイテム数 | {total_new} |")
    if error_sources:
        lines.append(f"| エラーソース | {', '.join(error_sources)} |")
    lines.append("")

    # 新規アイテム
    if total_new > 0:
        lines.append("## 新着情報\n")
        for source, items in new_items.items():
            if not items:
                continue
            source_name = items[0].source_name
            lines.append(f"### {source_name}\n")
            for item in items:
                date_str = f" ({item.published_date})" if item.published_date else ""
                lines.append(f"- **[{item.title}]({item.url})**{date_str}")
                if item.description:
                    # 長いdescriptionは切り詰め
                    desc = item.description[:200]
                    if len(item.description) > 200:
                        desc += "..."
                    lines.append(f"  - {desc}")
            lines.append("")

    # ソース別全件
    lines.append("## ソース別一覧\n")
    for r in results:
        lines.append(f"### {r.source_name} ({r.count}件)\n")
        if r.errors:
            for err in r.errors:
                lines.append(f"> **エラー**: {err}\n")

        if r.items:
            for item in r.items:
                date_str = f" ({item.published_date})" if item.published_date else ""
                cat_str = f" [{item.category}]" if item.category else ""
                lines.append(f"- [{item.title}]({item.url}){cat_str}{date_str}")
        else:
            lines.append("_アイテムなし_")
        lines.append("")

    # エラー詳細
    all_errors = []
    for r in results:
        for err in r.errors:
            all_errors.append(f"- **{r.source_name}**: {err}")

    if all_errors:
        lines.append("## エラー詳細\n")
        lines.extend(all_errors)
        lines.append("")

    content = "\n".join(lines)
    report_path.write_text(content, encoding="utf-8")
    return report_path


def generate_latest_symlink(output_dir: Path, report_path: Path) -> None:
    """latest.md シンボリックリンクを更新する"""
    latest = output_dir / "latest.md"
    if latest.is_symlink() or latest.exists():
        latest.unlink()
    latest.symlink_to(report_path.name)
