"""前回スナップショットとの差分から「新規ランクイン」「順位上昇」商品を検出する。

楽天ウェブサービスには実売数や検索サジェストを返す公開APIが無いため、
リアルタイムランキングを定期的に記録し、その変化をトレンドの代理指標として扱う。
"""
import json
from dataclasses import dataclass
from datetime import datetime, timezone

from config import DATA_DIR
from rakuten_client import RankedItem


@dataclass
class TrendItem:
    item: RankedItem
    status: str  # "new" | "up" | "steady"
    previous_rank: int | None


def _snapshot_path(genre_id: str) -> "str":
    return str(DATA_DIR / f"ranking_snapshot_{genre_id}.json")


def load_previous_ranks(genre_id: str) -> dict[str, int]:
    path = _snapshot_path(genre_id)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return {entry["item_code"]: entry["rank"] for entry in data.get("items", [])}
    except FileNotFoundError:
        return {}


def save_snapshot(genre_id: str, items: list[RankedItem]) -> None:
    path = _snapshot_path(genre_id)
    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "items": [{"item_code": i.item_code, "rank": i.rank, "name": i.name} for i in items],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def detect_trends(items: list[RankedItem], genre_id: str, top_n: int = 10) -> list[TrendItem]:
    """トレンド順(新規 > 上昇幅の大きい順)に並べたTrendItemを返す。

    初回実行(前回スナップショットが無い)場合は、現在の上位をそのまま返す。
    """
    previous_ranks = load_previous_ranks(genre_id)
    trends: list[TrendItem] = []

    for item in items:
        prev_rank = previous_ranks.get(item.item_code)
        if prev_rank is None:
            status = "new" if previous_ranks else "steady"
        elif prev_rank > item.rank:
            status = "up"
        else:
            status = "steady"
        trends.append(TrendItem(item=item, status=status, previous_rank=prev_rank))

    trends.sort(key=_sort_key)

    save_snapshot(genre_id, items)

    return trends[:top_n]


def _sort_key(t: TrendItem):
    priority = {"new": 0, "up": 1, "steady": 2}[t.status]
    gain = (t.previous_rank - t.item.rank) if t.previous_rank else 0
    return (priority, -gain, t.item.rank)


def merge_trends(trend_lists: list[list[TrendItem]], top_n: int = 10) -> list[TrendItem]:
    """複数ジャンルのトレンドリストを1つに統合し、優先度順に並べ直す。"""
    merged = [t for trends in trend_lists for t in trends]
    merged.sort(key=_sort_key)
    return merged[:top_n]
