"""政策情報ソース"""

from .jst import collect_jst
from .mext import collect_mext

# JSPS は著作権がJSPS帰属・無断転載禁止のため、許可取得まで無効化
# from .jsps import collect_jsps

__all__ = ["collect_jst", "collect_mext"]
