# ra-policy-collector

科学技術政策情報の自動収集システム -- リサーチアドミニストレーター(RA)向け

## 背景と目的

日本の大学のリサーチアドミニストレーター(RA)は、政府の科学技術政策情報（公募、予算、方針変更等）を各大学が個別に手動で収集している。これは非効率であり、全国の RA が同じ作業を繰り返している。

このツールは、主要な政府機関・資金配分機関の公開情報を自動で収集・構造化し、差分検出（新規公募の検知等）を行うことで、情報収集コストを大幅に削減することを目指す。

## 対象ソース

| ソース | 方式 | 対象情報 |
|--------|------|----------|
| 文部科学省（MEXT） | Webスクレイピング | 科学技術関連の公募情報 |
| 科学技術振興機構（JST） | RSSフィード | 公募情報全般 |
| 日本学術振興会（JSPS） | Webスクレイピング | 科研費公募情報 |

今後の拡張候補:
- 内閣府 CSTI（総合科学技術・イノベーション会議）
- e-Rad（府省共通研究開発管理システム）
- NEDO（新エネルギー・産業技術総合開発機構）
- AMED（日本医療研究開発機構）

## セットアップ

```bash
# uv がインストールされていない場合
curl -LsSf https://astral.sh/uv/install.sh | sh

# 依存関係のインストール
uv sync
```

## 使い方

```bash
# 収集を実行
uv run python -m ra_policy_collector.collector

# 結果の確認
# - data/ : JSON形式の構造化データ（ソース別）
# - output/ : Markdown形式のレポート
```

### 出力例

**data/jst.json** (構造化データ):
```json
[
  {
    "title": "戦略的創造研究推進事業 CREST 2026年度研究提案募集",
    "url": "https://www.jst.go.jp/kisoken/boshuu/teian.html",
    "source": "jst",
    "source_name": "科学技術振興機構（JST）",
    "published_date": "2026-04-08",
    "category": "公募"
  }
]
```

**output/2026-04-14-report.md** (Markdownレポート):
- サマリー（収集件数、新規件数、エラー）
- 新着情報（前回からの差分）
- ソース別一覧

## 自動実行（GitHub Actions）

毎日 JST 9:00 に自動収集が実行される（`.github/workflows/collect.yml`）。

手動で実行する場合は、GitHub の Actions タブから "科学技術政策情報の自動収集" ワークフローを選択し、"Run workflow" をクリック。

## プロジェクト構成

```
ra-policy-collector/
├── src/ra_policy_collector/
│   ├── __init__.py
│   ├── collector.py      # メインオーケストレーター
│   ├── models.py         # データモデル・差分検出
│   ├── report.py         # Markdownレポート生成
│   └── sources/
│       ├── __init__.py
│       ├── jst.py        # JST（RSSフィード）
│       ├── mext.py       # 文部科学省（スクレイピング）
│       └── jsps.py       # JSPS（スクレイピング）
├── data/                 # 収集データ（JSON）
├── output/               # 生成レポート（Markdown）
├── .github/workflows/
│   └── collect.yml       # GitHub Actions定期実行
├── pyproject.toml
└── README.md
```

## 新しいソースの追加方法

1. `src/ra_policy_collector/sources/` に新しいファイルを作成
2. `CollectionResult` を返す `collect_xxx()` 関数を実装
3. `sources/__init__.py` にインポートを追加
4. `collector.py` の `COLLECTORS` リストに追加

```python
# src/ra_policy_collector/sources/nedo.py の例
from ..models import CollectionResult, PolicyItem

def collect_nedo() -> CollectionResult:
    result = CollectionResult(source="nedo", source_name="NEDO")
    # ... 収集ロジック
    return result
```

## 注意事項

- 対象は全て公開情報であり、ログイン不要なページのみを収集する
- 各機関のサーバーに過度な負荷をかけないよう、適切な間隔を空けて収集する
- スクレイピング対象のページ構造が変更された場合、収集が失敗する可能性がある（エラーはレポートに記録される）

## ライセンス

MIT
